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
opaque_id: INC-ED6FA633D12F
observation_window={"duration_rel_s":2340.0,"source_metric_rows":40}
selection_summary={"candidate_count":63,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":1500,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["adservice","adservice-0","adservice-1","adservice-2","adservice-grpc","adservice-http","adservice2","adservice2-0","cartservice-0","cartservice-1","cartservice-2","cartservice-grpc","cartservice2-0","checkoutservice-0","checkoutservice-1","checkoutservice-2","checkoutservice-grpc","checkoutservice2-0","currencyservice-0","currencyservice-1","currencyservice-2","currencyservice-grpc","currencyservice2-0","emailservice-0","emailservice-1","emailservice-2","emailservice-grpc","emailservice2-0","frontend-0","frontend-1","frontend-2","frontend-http","frontend2-0","istio-egressgateway-7bfdcc9d86-zpjpg","istio-ingressgateway-565bffd4d-6bl7m","node-1","node-2","node-3","node-4","node-5","node-6","paymentservice-0","paymentservice-1","paymentservice-2","paymentservice-grpc","paymentservice2-0","productcatalogservice-0","productcatalogservice-1","productcatalogservice-2","productcatalogservice-grpc","productcatalogservice2-0","recommendationservice-0","recommendationservice-1","recommendationservice-2","recommendationservice-grpc","recommendationservice2-0","redis-cart-0","redis-cart2-0","shippingservice-0","shippingservice-1","shippingservice-2","shippingservice-grpc","shippingservice2-0"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[18.281,54.844,91.406,127.969,164.531,201.094,237.656,274.219,310.781,347.344,383.906,420.469,457.031,493.594,530.156,566.719,603.281,639.844,676.406,712.969,749.531,786.094,822.656,859.219,895.781,932.344,968.906,1005.469,1042.031,1078.594,1115.156,1151.719,1188.281,1224.844,1261.406,1297.969,1334.531,1371.094,1407.656,1444.219,1480.781,1517.344,1553.906,1590.469,1627.031,1663.594,1700.156,1736.719,1773.281,1809.844,1846.406,1882.969,1919.531,1956.094,1992.656,2029.219,2065.781,2102.344,2138.906,2175.469,2212.031,2248.594,2285.156,2321.719]
[M1] rank=1 service=adservice2 metric=java_lang_Memory_ObjectPendingFinalizationCount baseline=0.0 peak=1.583333 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1.583333,-1.583333,0,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M2] rank=2 service=frontend-0 metric=container_network_receive_packets_dropped.eth0 baseline=0.0 peak=3.0 signed_z=999.0 onset_bin=59 onset_rel_s=2175.469 persistence_bins=2
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1.5,1.5,-1.5,-1.5,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M3] rank=3 service=frontend-0 metric=istio_request_bytes.http.0. baseline=0.0 peak=670.0 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,670,-670,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M4] rank=4 service=frontend-0 metric=istio_request_duration_milliseconds.http.0. baseline=0.0 peak=121000.0 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,121000,-121000,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M5] rank=5 service=frontend-0 metric=istio_request_duration_milliseconds.http.200. baseline=4269.1125 peak=270424.25 signed_z=999.0 onset_bin=44 onset_rel_s=1627.031 persistence_bins=8
values_compact=delta:3960,0,342.75,149.25,-310.5,194,-349.75,333.25,85.75,232.75,-358.75,-73.75,286.75,-165.25,-48.25,210,-493.25,137.25,107.5,208.25,-93.75,-270.75,1141.5,-684,-621.5,234.25,470.5,255,191.25,-306.75,-16.5,265.75,-352,123.5,-266.5,486,76034.25,98401.25,90984.75,-263805.25
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M6] rank=6 service=frontend-0 metric=istio_requests.http.0. baseline=0.0 peak=2.0 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,2,-2,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M7] rank=7 service=frontend-1 metric=container_memory_failures.container.pgmajfault baseline=0.0 peak=22.0 signed_z=999.0 onset_bin=59 onset_rel_s=2175.469 persistence_bins=2
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,11,11,-22,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M8] rank=8 service=frontend-1 metric=container_memory_failures.hierarchy.pgmajfault baseline=0.0 peak=22.0 signed_z=999.0 onset_bin=59 onset_rel_s=2175.469 persistence_bins=2
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,11,11,-22,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M9] rank=9 service=frontend-1 metric=istio_request_bytes.http.0. baseline=0.0 peak=2390.0 signed_z=999.0 onset_bin=62 onset_rel_s=2285.156 persistence_bins=2
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,2390,-1167.5,-340
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M10] rank=10 service=frontend-1 metric=istio_request_duration_milliseconds.http.0. baseline=0.0 peak=422500.0 signed_z=999.0 onset_bin=62 onset_rel_s=2285.156 persistence_bins=2
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,422500,-211750,-60500
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M11] rank=11 service=frontend-1 metric=istio_requests.http.0. baseline=0.0 peak=7.0 signed_z=999.0 onset_bin=62 onset_rel_s=2285.156 persistence_bins=2
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,7,-3.5,-1
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M12] rank=12 service=frontend-2 metric=istio_request_bytes.http.0. baseline=0.0 peak=837.5 signed_z=999.0 onset_bin=59 onset_rel_s=2175.469 persistence_bins=2
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,167.5,670,-837.5,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[2040.0,2280.0]

=== LOG SUMMARY ===
{"entries":[{"error_logs":18,"error_pct":0.2,"service":"recommendationservice-0","total_logs":8852},{"error_logs":15,"error_pct":0.17,"service":"recommendationservice-2","total_logs":8834},{"error_logs":13,"error_pct":0.02,"service":"frontend-1","total_logs":55596},{"error_logs":12,"error_pct":0.14,"service":"recommendationservice-1","total_logs":8806},{"error_logs":3,"error_pct":0.0,"service":"frontend-2","total_logs":61583},{"error_logs":2,"error_pct":0.0,"service":"frontend-0","total_logs":57627}],"mode":"errors","omitted_services":25,"service_count":31}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":658356.2,"error_pct":0.0,"p95_during_ms":20385.8035,"p95_pre_ms":3.096,"service":"recommendationservice-2","spans":5470},{"delta_pct":461808.4,"error_pct":0.0,"p95_during_ms":14055.874,"p95_pre_ms":3.043,"service":"recommendationservice-1","spans":5475},{"delta_pct":13668.9,"error_pct":0.0,"p95_during_ms":416.9225,"p95_pre_ms":3.028,"service":"recommendationservice2-0","spans":4248},{"delta_pct":18.9,"error_pct":0.0,"p95_during_ms":0.31239999999999996,"p95_pre_ms":0.26280000000000003,"service":"emailservice-1","spans":152},{"delta_pct":13.2,"error_pct":0.0,"p95_during_ms":0.19679999999999997,"p95_pre_ms":0.17384999999999998,"service":"paymentservice-2","spans":153},{"delta_pct":11.5,"error_pct":0.0,"p95_during_ms":62.95449999999996,"p95_pre_ms":56.4756,"service":"frontend-2","spans":44464},{"delta_pct":11.1,"error_pct":0.0,"p95_during_ms":0.03,"p95_pre_ms":0.027,"service":"adservice-1","spans":2294},{"delta_pct":9.2,"error_pct":0.0,"p95_during_ms":47.86275,"p95_pre_ms":43.825,"service":"checkoutservice-1","spans":1796}],"omitted_services":32,"service_count":40}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=16 omitted_edges=1
[{"evidence_source":"metric","onset_rel_s":1440.0,"rank":1,"service":"adservice2","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1560.0,"rank":2,"service":"istio-egressgateway","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1560.0,"rank":3,"service":"emailservice2","severity_z":120.298},{"evidence_source":"metric","onset_rel_s":1620.0,"rank":4,"service":"paymentservice","severity_z":347.225},{"evidence_source":"metric","onset_rel_s":1860.0,"rank":5,"service":"node-1","severity_z":277.122},{"evidence_source":"metric","onset_rel_s":1920.0,"rank":6,"service":"redis-cart","severity_z":94.132},{"evidence_source":"metric","onset_rel_s":2100.0,"rank":7,"service":"productcatalogservice","severity_z":999.0},{"evidence_source":"trace","onset_rel_s":2120.4,"rank":8,"service":"recommendationservice","severity_z":999.0},{"evidence_source":"trace","onset_rel_s":2120.4,"rank":9,"service":"recommendationservice2","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":2160.0,"rank":10,"service":"node-6","severity_z":999.0},{"evidence_source":"trace","onset_rel_s":2169.6,"rank":11,"service":"frontend","severity_z":999.0},{"evidence_source":"trace","onset_rel_s":2169.6,"rank":12,"service":"frontend2","severity_z":999.0},{"evidence_source":"trace","onset_rel_s":2169.6,"rank":13,"service":"checkoutservice","severity_z":7.339},{"evidence_source":"trace","onset_rel_s":2266.8,"rank":14,"service":"shippingservice","severity_z":6.099}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"paymentservice","caller":"checkoutservice"},{"callee":"productcatalogservice","caller":"checkoutservice"},{"callee":"shippingservice","caller":"checkoutservice"},{"callee":"checkoutservice","caller":"frontend"},{"callee":"productcatalogservice","caller":"frontend"},{"callee":"recommendationservice","caller":"frontend"},{"callee":"shippingservice","caller":"frontend"},{"callee":"adservice2","caller":"frontend2"},{"callee":"recommendationservice2","caller":"frontend2"},{"callee":"productcatalogservice","caller":"recommendationservice"},{"callee":"productcatalogservice","caller":"recommendationservice2"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

{"confidence":"high","reason":"Rank shippingservice-1 first because shippingservice-1 has trace evidence at propagation rank 14; although frontend-0 is salient, the caller path frontend -> shippingservice means a disturbance in the callee can propagate back toward that caller-side symptom.","services":["shippingservice-1","frontend-0"]}

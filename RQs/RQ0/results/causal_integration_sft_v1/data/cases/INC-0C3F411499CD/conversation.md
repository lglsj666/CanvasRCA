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
opaque_id: INC-0C3F411499CD
observation_window={"duration_rel_s":2340.0,"source_metric_rows":40}
selection_summary={"candidate_count":63,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":1501,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["adservice","adservice-0","adservice-1","adservice-2","adservice-grpc","adservice-http","adservice2","adservice2-0","cartservice-0","cartservice-1","cartservice-2","cartservice-grpc","cartservice2-0","checkoutservice-0","checkoutservice-1","checkoutservice-2","checkoutservice-grpc","checkoutservice2-0","currencyservice-0","currencyservice-1","currencyservice-2","currencyservice-grpc","currencyservice2-0","emailservice-0","emailservice-1","emailservice-2","emailservice-grpc","emailservice2-0","frontend-0","frontend-1","frontend-2","frontend-http","frontend2-0","istio-egressgateway-7bfdcc9d86-22q7z","istio-ingressgateway-565bffd4d-4nr6v","node-1","node-2","node-3","node-4","node-5","node-6","paymentservice-0","paymentservice-1","paymentservice-2","paymentservice-grpc","paymentservice2-0","productcatalogservice-0","productcatalogservice-1","productcatalogservice-2","productcatalogservice-grpc","productcatalogservice2-0","recommendationservice-0","recommendationservice-1","recommendationservice-2","recommendationservice-grpc","recommendationservice2-0","redis-cart-0","redis-cart2-0","shippingservice-0","shippingservice-1","shippingservice-2","shippingservice-grpc","shippingservice2-0"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[18.281,54.844,91.406,127.969,164.531,201.094,237.656,274.219,310.781,347.344,383.906,420.469,457.031,493.594,530.156,566.719,603.281,639.844,676.406,712.969,749.531,786.094,822.656,859.219,895.781,932.344,968.906,1005.469,1042.031,1078.594,1115.156,1151.719,1188.281,1224.844,1261.406,1297.969,1334.531,1371.094,1407.656,1444.219,1480.781,1517.344,1553.906,1590.469,1627.031,1663.594,1700.156,1736.719,1773.281,1809.844,1846.406,1882.969,1919.531,1956.094,1992.656,2029.219,2065.781,2102.344,2138.906,2175.469,2212.031,2248.594,2285.156,2321.719]
[M1] rank=1 service=checkoutservice-0 metric=container_fs_writes./dev/vda baseline=0.0 peak=15.0 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,2.5,0,-2.5,0,0,4,-2,-2,0,0,0,15,-15,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M2] rank=2 service=checkoutservice-0 metric=container_fs_writes_MB./dev/vda baseline=0.0 peak=6.980469 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1.037109,0,-1.037109,0,0,1.692708,-0.846354,-0.846354,0,0,0,6.980469,-6.980469,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M3] rank=3 service=checkoutservice-0 metric=istio_request_bytes.grpc.200.13.0 baseline=0.0 peak=5495.0 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,5495,-5495,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001111111111100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,0,0,0,0,0,0,0,0,0,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M4] rank=4 service=checkoutservice-0 metric=istio_request_duration_milliseconds.grpc.200.13.0 baseline=0.0 peak=142500.0 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,142500,-142500,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001111111111100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,0,0,0,0,0,0,0,0,0,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M5] rank=5 service=checkoutservice-0 metric=istio_request_duration_milliseconds.http.202. baseline=0.1525 peak=213876.05 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,3.05,-3.05,0,0,0,0,0,0,0,0,0,0,213876.05,-213876.05,0,0,0,0,1.575,-1.05,-0.525,1.05,-1.05,0.525,1.05
missing_mask_bits=0010010100101001010010010100101001111111111100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,0,0,0,0,0,0,0,0,0,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M6] rank=6 service=checkoutservice-0 metric=istio_requests.grpc.200.13.0 baseline=0.0 peak=7.0 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,7,-7,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001111111111100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,0,0,0,0,0,0,0,0,0,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M7] rank=7 service=checkoutservice-0 metric=istio_response_bytes.grpc.200.13.0 baseline=0.0 peak=10050.0 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,10050,-10050,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001111111111100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,0,0,0,0,0,0,0,0,0,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M8] rank=8 service=frontend-0 metric=istio_request_bytes.http.0. baseline=0.0 peak=645.0 signed_z=999.0 onset_bin=41 onset_rel_s=1517.344 persistence_bins=3
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,645,-645,0,322.5,0,322.5,-645,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M9] rank=9 service=frontend-0 metric=istio_request_duration_milliseconds.http.0. baseline=0.0 peak=60500.0 signed_z=999.0 onset_bin=41 onset_rel_s=1517.344 persistence_bins=3
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,60500,-60500,0,30250,0,30250,-60500,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M10] rank=10 service=frontend-0 metric=istio_requests.http.0. baseline=0.0 peak=1.0 signed_z=999.0 onset_bin=41 onset_rel_s=1517.344 persistence_bins=3
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.5,0,-0.5,0,0.5,0,0.5,-1,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M11] rank=11 service=frontend-1 metric=istio_request_bytes.http.0. baseline=0.0 peak=645.0 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,645,-645,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M12] rank=12 service=frontend-1 metric=istio_request_duration_milliseconds.http.0. baseline=0.0 peak=60500.0 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,60500,-60500,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[1200.0,1680.0]

=== LOG SUMMARY ===
{"entries":[{"error_logs":16,"error_pct":2.53,"service":"checkoutservice-0","total_logs":632},{"error_logs":4,"error_pct":0.02,"service":"frontend-2","total_logs":18102},{"error_logs":3,"error_pct":0.01,"service":"frontend-0","total_logs":20268},{"error_logs":1,"error_pct":0.01,"service":"frontend-1","total_logs":10639}],"mode":"errors","omitted_services":27,"service_count":31}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":10773.2,"error_pct":0.0,"p95_during_ms":20009.423,"p95_pre_ms":184.02484999999987,"service":"checkoutservice-0","spans":428},{"delta_pct":78.8,"error_pct":0.0,"p95_during_ms":0.152,"p95_pre_ms":0.085,"service":"shippingservice-1","spans":293},{"delta_pct":-16.4,"error_pct":0.0,"p95_during_ms":0.2265,"p95_pre_ms":0.27104999999999985,"service":"emailservice-1","spans":40},{"delta_pct":-12.8,"error_pct":0.0,"p95_during_ms":0.21575,"p95_pre_ms":0.24729999999999996,"service":"emailservice-2","spans":41},{"delta_pct":-9.0,"error_pct":0.0,"p95_during_ms":0.13725,"p95_pre_ms":0.15075,"service":"paymentservice-2","spans":40},{"delta_pct":-6.1,"error_pct":0.0,"p95_during_ms":0.1574,"p95_pre_ms":0.16754999999999992,"service":"paymentservice2-0","spans":74},{"delta_pct":-5.9,"error_pct":0.0,"p95_during_ms":0.133,"p95_pre_ms":0.1414,"service":"paymentservice-0","spans":40},{"delta_pct":5.9,"error_pct":0.0,"p95_during_ms":0.08579999999999999,"p95_pre_ms":0.081,"service":"shippingservice-2","spans":295}],"omitted_services":32,"service_count":40}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=13 omitted_edges=0
[{"evidence_source":"metric","onset_rel_s":1200.0,"rank":1,"service":"recommendationservice","severity_z":55.25},{"evidence_source":"trace","onset_rel_s":1243.2,"rank":2,"service":"checkoutservice","severity_z":685.267},{"evidence_source":"metric","onset_rel_s":1260.0,"rank":3,"service":"paymentservice","severity_z":179.408},{"evidence_source":"trace","onset_rel_s":1291.8,"rank":4,"service":"cartservice2","severity_z":6.158},{"evidence_source":"metric","onset_rel_s":1320.0,"rank":5,"service":"frontend","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1380.0,"rank":6,"service":"emailservice","severity_z":84.645},{"evidence_source":"metric","onset_rel_s":1380.0,"rank":7,"service":"currencyservice","severity_z":56.883},{"evidence_source":"metric","onset_rel_s":1560.0,"rank":8,"service":"cartservice","severity_z":49.47},{"evidence_source":"metric","onset_rel_s":1620.0,"rank":9,"service":"recommendationservice2","severity_z":49.31},{"evidence_source":"trace","onset_rel_s":1633.2,"rank":10,"service":"shippingservice2","severity_z":11.983},{"evidence_source":"metric","onset_rel_s":1680.0,"rank":11,"service":"redis-cart2","severity_z":95.929},{"evidence_source":"metric","onset_rel_s":1920.0,"rank":12,"service":"node-6","severity_z":45.724},{"evidence_source":"trace","onset_rel_s":2023.2,"rank":13,"service":"adservice","severity_z":6.759},{"evidence_source":"metric","onset_rel_s":2040.0,"rank":14,"service":"node-4","severity_z":33.853}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"cartservice","caller":"checkoutservice"},{"callee":"currencyservice","caller":"checkoutservice"},{"callee":"emailservice","caller":"checkoutservice"},{"callee":"paymentservice","caller":"checkoutservice"},{"callee":"adservice","caller":"frontend"},{"callee":"cartservice","caller":"frontend"},{"callee":"checkoutservice","caller":"frontend"},{"callee":"currencyservice","caller":"frontend"},{"callee":"recommendationservice","caller":"frontend"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

{"confidence":"high","reason":"Rank checkoutservice-0 first because checkoutservice-0 has direct container_fs_writes./dev/vda evidence (signed-z 999, persistence 0 bins); although frontend-0 is salient, the caller path frontend -> checkoutservice means a disturbance in the callee can propagate back toward that caller-side symptom.","services":["checkoutservice-0","frontend-0"]}

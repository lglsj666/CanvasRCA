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
opaque_id: INC-BFAC08D2206D
observation_window={"duration_rel_s":2340.0,"source_metric_rows":40}
selection_summary={"candidate_count":63,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":1460,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["adservice","adservice-0","adservice-1","adservice-2","adservice-grpc","adservice-http","adservice2","adservice2-0","cartservice-0","cartservice-1","cartservice-2","cartservice-grpc","cartservice2-0","checkoutservice-0","checkoutservice-1","checkoutservice-2","checkoutservice-grpc","checkoutservice2-0","currencyservice-0","currencyservice-1","currencyservice-2","currencyservice-grpc","currencyservice2-0","emailservice-0","emailservice-1","emailservice-2","emailservice-grpc","emailservice2-0","frontend-0","frontend-1","frontend-2","frontend-http","frontend2-0","istio-egressgateway-7bfdcc9d86-22q7z","istio-ingressgateway-565bffd4d-4nr6v","node-1","node-2","node-3","node-4","node-5","node-6","paymentservice-0","paymentservice-1","paymentservice-2","paymentservice-grpc","paymentservice2-0","productcatalogservice-0","productcatalogservice-1","productcatalogservice-2","productcatalogservice-grpc","productcatalogservice2-0","recommendationservice-0","recommendationservice-1","recommendationservice-2","recommendationservice-grpc","recommendationservice2-0","redis-cart-0","redis-cart2-0","shippingservice-0","shippingservice-1","shippingservice-2","shippingservice-grpc","shippingservice2-0"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[18.281,54.844,91.406,127.969,164.531,201.094,237.656,274.219,310.781,347.344,383.906,420.469,457.031,493.594,530.156,566.719,603.281,639.844,676.406,712.969,749.531,786.094,822.656,859.219,895.781,932.344,968.906,1005.469,1042.031,1078.594,1115.156,1151.719,1188.281,1224.844,1261.406,1297.969,1334.531,1371.094,1407.656,1444.219,1480.781,1517.344,1553.906,1590.469,1627.031,1663.594,1700.156,1736.719,1773.281,1809.844,1846.406,1882.969,1919.531,1956.094,1992.656,2029.219,2065.781,2102.344,2138.906,2175.469,2212.031,2248.594,2285.156,2321.719]
[M1] rank=1 service=adservice-0 metric=istio_request_duration_milliseconds.grpc.200.0.0 baseline=17.80375 peak=3187.5 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:16.4,1.475,1.05,-6.65,9.725,-8.2,3.6,-3.05,8.625,-8.15,6.675,-7.15,7.15,-3.6,-1,4.6,-2.55,-1.575,3.075,-5.625,1478.825,1693.85,-1904.825,-1264.275,-3.575,7.175,-11.25,8.2,-0.575,5.65,-12.75,6.15,-5.125,9.175,-9.175,7.15,-9.2,12.25,-11.75,9.2
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M2] rank=2 service=adservice-0 metric=istio_request_duration_milliseconds.http.202. baseline=0.155 peak=3187.5 signed_z=999.0 onset_bin=36 onset_rel_s=1334.531 persistence_bins=2
values_compact=delta:0,1.025,0,-1.025,0,0,0,0,0,0,0,0,0.525,0,-0.525,0,0,0,0,0,1487.5,1700,-1911.975,-1273.975,-0.525,-1.025,0,0,1.05,0,-1.05,0,0,1.05,-1.05,0,0,0,0,0.525
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M3] rank=3 service=adservice-1 metric=istio_request_duration_milliseconds.grpc.200.0.0 baseline=17.87875 peak=2975.0 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:17.4,-1.025,0.025,-0.55,4.075,-4.575,1.525,-2.025,4.575,-3.05,5.1,-4.1,3.6,-4.075,1.525,3.575,-2.575,-3.55,4.6,-4.65,1480.35,1478.825,-1903.825,-1050.75,-4.575,6.15,-11.25,7.7,-5.125,7.175,-8.2,8.15,-8.15,9.15,-6.625,4.625,-9.725,14.3,-14.3,10.725
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M4] rank=4 service=adservice-1 metric=istio_request_duration_milliseconds.http.202. baseline=0.575 peak=2975.0 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,1.05,-0.525,0,1.05,-1.05,-0.525,1.025,0,0.025,0,-1.05,0,1.05,-0.525,0,-0.525,1.05,1487.5,1486.45,-1911.975,-1061.45,-0.525,-1.05,0,0,0,0,0,1.05,-1.05,3.075,-1.525,-0.5,-0.525,0.525,-1.05,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M5] rank=5 service=adservice-2 metric=istio_request_duration_milliseconds.grpc.200.0.0 baseline=17.055 peak=3187.5 signed_z=999.0 onset_bin=59 onset_rel_s=2175.469 persistence_bins=2
values_compact=delta:16.4,0,1,-3.05,3.05,-2.025,-1.025,0,4.6,-3.1,4.625,-5.125,5.15,-3.075,2,0.05,-2.05,-0.025,2.075,-6.15,633.4,2540.775,-1482.375,-1688.75,-1,5.125,-10.25,8.2,-4.1,6.15,-9.225,10.7,-8.15,3.6,-4.1,5.125,-9.225,14.3,-11.8,10.275
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M6] rank=6 service=adservice-2 metric=istio_request_duration_milliseconds.http.202. baseline=0.2625 peak=3187.5 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,1.05,-1.05,0,0,0,0,0.525,1.05,-1.05,0,-0.525,0,0,0,0,1.05,-1.05,0,637.5,2550,-1487.5,-1698.95,-1.05,0,0,0,0,0,0,2.05,-2.05,0,0,0,0,0.525,1.025,-0.525
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M7] rank=7 service=adservice2-0 metric=istio_request_bytes.grpc.200.4.0 baseline=0.0 peak=952.5 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,942.5,10,-952.5,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M8] rank=8 service=adservice2-0 metric=istio_request_duration_milliseconds.grpc.200.0.0 baseline=133.0625 peak=22312.5 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:138.25,-13.7,18.325,-24.45,6.225,8.075,3.425,-14.8,9.75,6.1,-1.45,-1.525,-10.75,14.4,-11.375,20.9,-10.15,-9.05,10.1,6.7,14545.025,7622.475,-18398.75,-3778.025,-32.075,50.45,-23.8,5.525,9.625,-42.275,26.525,-7.675,14.15,6.65,-14.75,-0.45,-7.175,7.65,-13.75,32.225
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M9] rank=9 service=adservice2-0 metric=istio_request_duration_milliseconds.grpc.200.4.0 baseline=0.0 peak=757.5 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,757.5,0,-757.5,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M10] rank=10 service=adservice2-0 metric=istio_request_duration_milliseconds.http.202. baseline=1.7 peak=23260.0 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:2.1,-1.575,3.1,-2.05,-0.525,-0.525,2.1,-0.525,-0.525,1.575,-1.1,-1,-1.05,1.05,1.05,-1.05,1.05,0.525,-1.575,1.025,15719.475,7538.45,-19433.425,-3823.95,-1.575,2.1,-1.05,1.575,1.525,-2.575,-0.525,-0.525,2.075,1.05,-3.125,-1.575,1.05,-1.05,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M11] rank=11 service=adservice2-0 metric=istio_requests.grpc.200.4.0 baseline=0.0 peak=1.5 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1.5,0,-1.5,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M12] rank=12 service=adservice2-0 metric=istio_response_bytes.grpc.200.4.0 baseline=0.0 peak=1725.0 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1725,0,-1725,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[1140.0,1380.0]

=== LOG SUMMARY ===
{"entries":[{"error_logs":24,"error_pct":0.29,"service":"frontend-0","total_logs":8154},{"error_logs":20,"error_pct":0.25,"service":"frontend-1","total_logs":8061},{"error_logs":17,"error_pct":0.21,"service":"frontend-2","total_logs":8204}],"mode":"errors","omitted_services":28,"service_count":31}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":983.3,"error_pct":0.0,"p95_during_ms":500.11060000000003,"p95_pre_ms":46.16340000000001,"service":"frontend2-0","spans":38841},{"delta_pct":938.0,"error_pct":0.0,"p95_during_ms":499.89515,"p95_pre_ms":48.15814999999999,"service":"frontend-1","spans":5640},{"delta_pct":932.2,"error_pct":0.0,"p95_during_ms":500.13065,"p95_pre_ms":48.4548,"service":"frontend-0","spans":5731},{"delta_pct":61.0,"error_pct":0.0,"p95_during_ms":0.22339999999999954,"p95_pre_ms":0.13879999999999992,"service":"shippingservice-2","spans":142},{"delta_pct":-47.7,"error_pct":0.0,"p95_during_ms":0.13555,"p95_pre_ms":0.25899999999999956,"service":"paymentservice-1","spans":19},{"delta_pct":-43.9,"error_pct":0.0,"p95_during_ms":22.678599999999975,"p95_pre_ms":40.41705,"service":"checkoutservice-1","spans":244},{"delta_pct":-26.3,"error_pct":0.0,"p95_during_ms":0.209,"p95_pre_ms":0.28339999999999993,"service":"emailservice-1","spans":20},{"delta_pct":19.3,"error_pct":0.0,"p95_during_ms":58.1886,"p95_pre_ms":48.75685,"service":"frontend-2","spans":5747}],"omitted_services":32,"service_count":40}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=15 omitted_edges=0
[{"evidence_source":"metric","onset_rel_s":1200.0,"rank":1,"service":"adservice2","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1200.0,"rank":2,"service":"currencyservice","severity_z":89.888},{"evidence_source":"trace","onset_rel_s":1243.2,"rank":3,"service":"frontend","severity_z":102.997},{"evidence_source":"trace","onset_rel_s":1243.2,"rank":4,"service":"frontend2","severity_z":107.503},{"evidence_source":"metric","onset_rel_s":1260.0,"rank":5,"service":"adservice","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1260.0,"rank":6,"service":"paymentservice","severity_z":304.788},{"evidence_source":"metric","onset_rel_s":1320.0,"rank":7,"service":"node-5","severity_z":166.667},{"evidence_source":"metric","onset_rel_s":1440.0,"rank":8,"service":"node-1","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1440.0,"rank":9,"service":"istio-egressgateway","severity_z":597.837},{"evidence_source":"metric","onset_rel_s":1440.0,"rank":10,"service":"paymentservice2","severity_z":101.248},{"evidence_source":"metric","onset_rel_s":1500.0,"rank":11,"service":"node-6","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1560.0,"rank":12,"service":"cartservice","severity_z":159.736},{"evidence_source":"metric","onset_rel_s":1680.0,"rank":13,"service":"shippingservice","severity_z":171.286},{"evidence_source":"metric","onset_rel_s":1740.0,"rank":14,"service":"checkoutservice2","severity_z":999.0}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"paymentservice2","caller":"checkoutservice2"},{"callee":"adservice","caller":"frontend"},{"callee":"cartservice","caller":"frontend"},{"callee":"currencyservice","caller":"frontend"},{"callee":"shippingservice","caller":"frontend"},{"callee":"adservice2","caller":"frontend2"},{"callee":"checkoutservice2","caller":"frontend2"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

{"confidence":"high","reason":"Rank adservice first because adservice has direct istio_request_duration_milliseconds.grpc.200.0.0 evidence (signed-z 999, persistence 0 bins); although frontend-0 is salient, the caller path frontend -> adservice means a disturbance in the callee can propagate back toward that caller-side symptom.","services":["adservice","frontend-0"]}

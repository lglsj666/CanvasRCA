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
opaque_id: INC-8E21E81E5921
observation_window={"duration_rel_s":2340.0,"source_metric_rows":40}
selection_summary={"candidate_count":63,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":1503,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["adservice","adservice-0","adservice-1","adservice-2","adservice-grpc","adservice-http","adservice2","adservice2-0","cartservice-0","cartservice-1","cartservice-2","cartservice-grpc","cartservice2-0","checkoutservice-0","checkoutservice-1","checkoutservice-2","checkoutservice-grpc","checkoutservice2-0","currencyservice-0","currencyservice-1","currencyservice-2","currencyservice-grpc","currencyservice2-0","emailservice-0","emailservice-1","emailservice-2","emailservice-grpc","emailservice2-0","frontend-0","frontend-1","frontend-2","frontend-http","frontend2-0","istio-egressgateway-7bfdcc9d86-zpjpg","istio-ingressgateway-565bffd4d-6bl7m","node-1","node-2","node-3","node-4","node-5","node-6","paymentservice-0","paymentservice-1","paymentservice-2","paymentservice-grpc","paymentservice2-0","productcatalogservice-0","productcatalogservice-1","productcatalogservice-2","productcatalogservice-grpc","productcatalogservice2-0","recommendationservice-0","recommendationservice-1","recommendationservice-2","recommendationservice-grpc","recommendationservice2-0","redis-cart-0","redis-cart2-0","shippingservice-0","shippingservice-1","shippingservice-2","shippingservice-grpc","shippingservice2-0"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[18.281,54.844,91.406,127.969,164.531,201.094,237.656,274.219,310.781,347.344,383.906,420.469,457.031,493.594,530.156,566.719,603.281,639.844,676.406,712.969,749.531,786.094,822.656,859.219,895.781,932.344,968.906,1005.469,1042.031,1078.594,1115.156,1151.719,1188.281,1224.844,1261.406,1297.969,1334.531,1371.094,1407.656,1444.219,1480.781,1517.344,1553.906,1590.469,1627.031,1663.594,1700.156,1736.719,1773.281,1809.844,1846.406,1882.969,1919.531,1956.094,1992.656,2029.219,2065.781,2102.344,2138.906,2175.469,2212.031,2248.594,2285.156,2321.719]
[M1] rank=1 service=adservice metric=java_lang_GarbageCollector_LastGcInfo_memoryUsageBeforeGc_used.Tenured_Gen.Copy baseline=54844275.333333 peak=55247312.0 signed_z=999.0 onset_bin=36 onset_rel_s=1334.531 persistence_bins=18
values_compact=delta:54843960,114.666667,229.333333,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,167570,33630,10.666667,53.333333,66773.333333,133586.666667,0,0,0,378.666667,506.666666,53.333334,57.333333,212,32,64,0,60,20,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M2] rank=2 service=checkoutservice-0 metric=container_network_receive_packets_dropped.eth0 baseline=0.0 peak=1.0 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,-1
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M3] rank=3 service=checkoutservice-1 metric=container_network_receive_packets_dropped.eth0 baseline=0.0 peak=0.5 signed_z=999.0 onset_bin=62 onset_rel_s=2285.156 persistence_bins=2
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.5,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M4] rank=4 service=emailservice-0 metric=container_cpu_usage_seconds baseline=0.026899 peak=14.238693 signed_z=999.0 onset_bin=62 onset_rel_s=2285.156 persistence_bins=2
values_compact=delta:0.029647,-0.002908,-0.001081,0.001081,0.001499,-0.001499,-0.000384,0.000932,-0.001963,0.002407,-0.002287,0.002499,-0.002737,0.002743,0,-0.00517,0.006365,-0.000501,0.002863,-0.010552,0.008619,-0.000221,-0.004142,0.001218,0.001512,-0.002199,0.008624,-0.013632,0.012171,-0.011566,0.007471,-0.001127,0.000102,0.004484,-0.006397,-0.000694,0.004436,1.164114,10.606775,2.438191
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M5] rank=5 service=emailservice-0 metric=container_cpu_user_seconds baseline=0.01975 peak=14.5 signed_z=999.0 onset_bin=62 onset_rel_s=2285.156 persistence_bins=2
values_compact=delta:0.025,-0.005,-0.005,0.005,0,0.005,-0.005,-0.005,0.01,-0.005,-0.005,0.005,-0.005,0.005,0,-0.01,0.01,0.005,0,-0.005,0,0.01,-0.015,0,0.01,-0.01,0.015,-0.02,0.01,0,0,0,0,0.01,-0.01,0.005,0,1.185,10.795,2.495
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M6] rank=6 service=emailservice-0 metric=istio_request_duration_milliseconds.http.202. baseline=0.0525 peak=1575.0 signed_z=999.0 onset_bin=21 onset_rel_s=786.094 persistence_bins=7
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0.525,0,-0.525,0,0,0,0,0,0,0,0,0,0,0.525,0,-0.525,0,0,0,0,0,1.05,-1.05,0,0,1575,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M7] rank=7 service=emailservice-1 metric=container_cpu_usage_seconds baseline=0.039245 peak=12.578292 signed_z=999.0 onset_bin=62 onset_rel_s=2285.156 persistence_bins=2
values_compact=delta:0.032462,0.017012,-0.020695,0.012141,-0.002728,0.004522,-0.004329,-0.002284,0.005722,-0.002621,0.004205,-0.005461,0.000721,-0.00048,0,0.001323,0.006733,-0.007329,-0.000764,-0.000519,-0.000949,0.007734,-0.005812,0.004175,0.000513,-0.009921,0.005992,0.00506,-0.008092,0.002381,0.004245,-0.007223,0.006771,0.003474,-0.012311,0.001974,0.011967,-0.012547,4.82597,7.71726
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M8] rank=8 service=emailservice-1 metric=container_cpu_user_seconds baseline=0.0205 peak=12.795 signed_z=999.0 onset_bin=62 onset_rel_s=2285.156 persistence_bins=2
values_compact=delta:0.015,0.005,0,0.005,-0.01,0.01,-0.01,0.005,0,-0.005,0.01,-0.005,0,0,0,0,0.005,0,0.005,-0.015,0.01,0.005,-0.02,0.015,0,-0.005,0.01,-0.01,-0.005,0,0.01,-0.01,0.015,-0.01,0,-0.005,0.015,-0.015,4.915,7.865
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M9] rank=9 service=emailservice2-0 metric=istio_request_duration_milliseconds.http.202. baseline=0.105 peak=13257.5 signed_z=999.0 onset_bin=62 onset_rel_s=2285.156 persistence_bins=2
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,1.05,-1.05,0,0,0,0,0.525,0,-0.525,0,1.05,-0.525,0,-0.525,2.05,-2.05,1.05,-1.05,0,0,0,0,0,0,0,0,215,317.55,12724.95
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M10] rank=10 service=node-1 metric=system.disk.pct_usage baseline=46.65 peak=46.64 signed_z=-999.0 onset_bin=36 onset_rel_s=1334.531 persistence_bins=4
values_compact=delta:46.65,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,-0.01,0,0,0,0,0,0.01,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M11] rank=11 service=node-4 metric=system.disk.pct_usage baseline=43.16 peak=43.17 signed_z=999.0 onset_bin=54 onset_rel_s=1992.656 persistence_bins=5
values_compact=delta:43.16,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.01,0,0,0,0,0,0
missing_mask_bits=0110010110101011010111010101101011010011100101101011010011100101
observed_counts_compact=csv:1,0,0,1,1,0,1,0,0,1,0,1,0,1,0,0,1,0,1,0,0,0,1,0,1,0,1,0,0,1,0,1,0,0,1,0,1,1,0,0,0,1,1,0,1,0,0,1,0,1,0,0,1,0,1,1,0,0,0,1,1,0,1,0
[M12] rank=12 service=node-6 metric=system.net.udp.in_errors baseline=0.0 peak=0.47 signed_z=999.0 onset_bin=62 onset_rel_s=2285.156 persistence_bins=2
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.15,0.32,-0.15
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[1140.0,2340.0]

=== LOG SUMMARY ===
{"entries":[{"error_logs":9,"error_pct":2.55,"service":"emailservice-2","total_logs":353},{"error_logs":6,"error_pct":1.85,"service":"emailservice-0","total_logs":325},{"error_logs":6,"error_pct":1.8,"service":"emailservice-1","total_logs":333}],"mode":"errors","omitted_services":28,"service_count":31}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":-100.0,"error_pct":0.0,"p95_during_ms":0.0,"p95_pre_ms":1.0,"service":"cartservice-2","spans":4894},{"delta_pct":-16.0,"error_pct":0.0,"p95_during_ms":0.1755,"p95_pre_ms":0.20899999999999988,"service":"paymentservice-2","spans":98},{"delta_pct":-15.4,"error_pct":0.0,"p95_during_ms":0.022,"p95_pre_ms":0.026,"service":"adservice-1","spans":1472},{"delta_pct":-12.0,"error_pct":0.0,"p95_during_ms":0.02025,"p95_pre_ms":0.023,"service":"adservice-2","spans":1471},{"delta_pct":-7.3,"error_pct":0.0,"p95_during_ms":0.2584,"p95_pre_ms":0.27879999999999994,"service":"emailservice-0","spans":94},{"delta_pct":-4.8,"error_pct":0.0,"p95_during_ms":0.08379999999999996,"p95_pre_ms":0.088,"service":"shippingservice-0","spans":680},{"delta_pct":4.5,"error_pct":0.0,"p95_during_ms":46.1505,"p95_pre_ms":44.14675,"service":"checkoutservice-1","spans":1152},{"delta_pct":3.6,"error_pct":0.0,"p95_during_ms":45.25244999999994,"p95_pre_ms":43.693949999999994,"service":"checkoutservice2-0","spans":5404}],"omitted_services":32,"service_count":40}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=14 omitted_edges=1
[{"evidence_source":"metric","onset_rel_s":1200.0,"rank":1,"service":"node-1","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1200.0,"rank":2,"service":"shippingservice","severity_z":173.146},{"evidence_source":"metric","onset_rel_s":1200.0,"rank":3,"service":"currencyservice","severity_z":106.054},{"evidence_source":"metric","onset_rel_s":1200.0,"rank":4,"service":"redis-cart","severity_z":99.151},{"evidence_source":"trace","onset_rel_s":1243.2,"rank":5,"service":"checkoutservice","severity_z":193.577},{"evidence_source":"metric","onset_rel_s":1440.0,"rank":6,"service":"adservice","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1440.0,"rank":7,"service":"cartservice","severity_z":134.69},{"evidence_source":"metric","onset_rel_s":1680.0,"rank":8,"service":"paymentservice","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1680.0,"rank":9,"service":"paymentservice2","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1800.0,"rank":10,"service":"node-4","severity_z":999.0},{"evidence_source":"trace","onset_rel_s":2266.8,"rank":11,"service":"emailservice","severity_z":193.559},{"evidence_source":"trace","onset_rel_s":2266.8,"rank":12,"service":"emailservice2","severity_z":113.345},{"evidence_source":"trace","onset_rel_s":2266.8,"rank":13,"service":"checkoutservice2","severity_z":80.084},{"evidence_source":"metric","onset_rel_s":2280.0,"rank":14,"service":"node-6","severity_z":999.0}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"cartservice","caller":"checkoutservice"},{"callee":"currencyservice","caller":"checkoutservice"},{"callee":"emailservice","caller":"checkoutservice"},{"callee":"paymentservice","caller":"checkoutservice"},{"callee":"shippingservice","caller":"checkoutservice"},{"callee":"emailservice2","caller":"checkoutservice2"},{"callee":"paymentservice2","caller":"checkoutservice2"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

{"confidence":"high","reason":"Rank paymentservice-0 first because paymentservice-0 has metric evidence at propagation rank 8; although checkoutservice-0 is salient, the caller path checkoutservice -> paymentservice means a disturbance in the callee can propagate back toward that caller-side symptom.","services":["paymentservice-0","checkoutservice-0"]}

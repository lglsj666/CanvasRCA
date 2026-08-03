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
opaque_id: INC-0A0D1DB84212
observation_window={"duration_rel_s":2340.0,"source_metric_rows":40}
selection_summary={"candidate_count":63,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":1515,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["adservice","adservice-0","adservice-1","adservice-2","adservice-grpc","adservice-http","adservice2","adservice2-0","cartservice-0","cartservice-1","cartservice-2","cartservice-grpc","cartservice2-0","checkoutservice-0","checkoutservice-1","checkoutservice-2","checkoutservice-grpc","checkoutservice2-0","currencyservice-0","currencyservice-1","currencyservice-2","currencyservice-grpc","currencyservice2-0","emailservice-0","emailservice-1","emailservice-2","emailservice-grpc","emailservice2-0","frontend-0","frontend-1","frontend-2","frontend-http","frontend2-0","istio-egressgateway-7bfdcc9d86-22q7z","istio-ingressgateway-565bffd4d-4nr6v","node-1","node-2","node-3","node-4","node-5","node-6","paymentservice-0","paymentservice-1","paymentservice-2","paymentservice-grpc","paymentservice2-0","productcatalogservice-0","productcatalogservice-1","productcatalogservice-2","productcatalogservice-grpc","productcatalogservice2-0","recommendationservice-0","recommendationservice-1","recommendationservice-2","recommendationservice-grpc","recommendationservice2-0","redis-cart-0","redis-cart2-0","shippingservice-0","shippingservice-1","shippingservice-2","shippingservice-grpc","shippingservice2-0"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[18.281,54.844,91.406,127.969,164.531,201.094,237.656,274.219,310.781,347.344,383.906,420.469,457.031,493.594,530.156,566.719,603.281,639.844,676.406,712.969,749.531,786.094,822.656,859.219,895.781,932.344,968.906,1005.469,1042.031,1078.594,1115.156,1151.719,1188.281,1224.844,1261.406,1297.969,1334.531,1371.094,1407.656,1444.219,1480.781,1517.344,1553.906,1590.469,1627.031,1663.594,1700.156,1736.719,1773.281,1809.844,1846.406,1882.969,1919.531,1956.094,1992.656,2029.219,2065.781,2102.344,2138.906,2175.469,2212.031,2248.594,2285.156,2321.719]
[M1] rank=1 service=cartservice-1 metric=container_cpu_cfs_throttled_seconds baseline=0.0 peak=0.043993 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.043993,-0.043993,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M2] rank=2 service=node-5 metric=system.process.zombie.num baseline=0.0 peak=1.0 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,-1,0,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M3] rank=3 service=productcatalogservice-1 metric=container_cpu_cfs_throttled_seconds baseline=0.0 peak=0.002488 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.002488,0,-0.002488,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M4] rank=4 service=paymentservice2-0 metric=container_network_receive_MB.eth0 baseline=0.019017 peak=0.539055 signed_z=258.026 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.020424,-0.000793,0.001587,-0.006259,0.009838,-0.005574,0.000063,-0.000264,-0.00045,-0.002062,0.001279,0.002203,-0.00147,0.000132,0.000468,-0.001631,0.002312,-0.003156,0.004413,-0.00345,-0.00115,0.002412,0.000931,-0.003782,0.003803,0.001092,0.518139,-0.523097,0.003659,-0.001544,0.00153,0.000345,-0.004852,0.002708,0.002276,0.000397,-0.001706,0.001927,-0.001563,-0.002519
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M5] rank=5 service=paymentservice-0 metric=container_network_receive_MB.eth0 baseline=0.02258 peak=0.546311 signed_z=177.586 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.021342,0.00323,0.002424,-0.000945,-0.010337,0.006868,-0.001543,-0.001225,0.0027,-0.002585,0.002884,0.001813,-0.000719,0.002652,-0.006736,0.007326,-0.004652,-0.004083,0.002629,0.003173,0.00604,-0.005873,-0.00872,0.013012,0.517636,-0.528447,0.002908,0.004886,0.003035,-0.005531,-0.001359,0.003486,-0.002349,-0.001221,0.002894,0.001819,0.000842,-0.011095,0.003821,0.005036
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M6] rank=6 service=shippingservice2-0 metric=container_network_receive_MB.eth0 baseline=0.02142 peak=0.280373 signed_z=62.416 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.030091,-0.0042,0.004259,-0.003482,-0.001784,-0.001637,-0.001241,-0.001324,-0.001906,0.000092,0.000878,-0.003827,0.00597,-0.00437,0.002306,-0.002175,0.000446,0.00246,0.000113,-0.005411,0.001959,0.005848,-0.008546,0.005061,0.00384,-0.000865,0.257818,-0.003324,-0.258273,0.00115,-0.001263,0.001307,-0.000976,-0.001425,-0.001729,0.008405,-0.005188,-0.000063,-0.00182,0.002278
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M7] rank=7 service=cartservice2-0 metric=container_network_receive_MB.eth0 baseline=0.029393 peak=0.54558 signed_z=40.771 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.051984,-0.005736,0.012505,-0.013495,0.002488,-0.018099,0.002987,-0.00664,-0.005886,0.001208,-0.000014,-0.002975,0.00342,0.001694,-0.006468,0.004585,-0.002176,0.002448,-0.002963,0.005875,0.001486,0.519352,-0.523641,-0.00225,0.000643,0.002398,-0.004308,0.003046,0.001015,-0.000781,-0.003905,0.004289,-0.002851,0.005359,-0.003759,-0.001146,0.001556,-0.002214,0.002797,0.000632
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M8] rank=8 service=node-3 metric=system.net.tcp.in_segs baseline=78.032 peak=137.08 signed_z=38.005 onset_bin=36 onset_rel_s=1334.531 persistence_bins=2
values_compact=delta:75.95,1.23,1.22,-0.62,-0.66,-0.91,0.59,0.22,0.95,0.79,-0.91,-0.74,1.34,0.02,1.02,-2.07,0.04,1.06,0.63,4.38,-3.8,-0.58,8.7,49.23,-59.08,0.37,-1.21,2.22,-1.5,1.35,-2.08,0.9,-0.26,-0.02,1.1,-0.84,-0.68,-0.04,0.72,1.47
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M9] rank=9 service=paymentservice-2 metric=container_memory_failures.container.pgfault baseline=50.016667 peak=687.0 signed_z=35.887 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:58,-0.5,-3.5,-9,-16,-8.5,8.5,2,31,7.5,-40,24.833333,14.833334,8.333333,-36.5,25.5,-25.5,29,-45.5,46.833333,-2.666666,235.833333,-268.5,30,-36.5,39.166667,3.166666,-22.333333,8.5,-17,40.5,-40,20,-16.5,642,-634,-7.5,-3.5,23.666667,5.666666
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M10] rank=10 service=paymentservice-2 metric=container_memory_failures.hierarchy.pgfault baseline=50.016667 peak=687.0 signed_z=35.887 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:58,-0.5,-3.5,-9,-16,-8.5,8.5,2,31,7.5,-40,24.833333,14.833334,8.333333,-36.5,25.5,-25.5,29,-45.5,46.833333,-2.666666,235.833333,-268.5,30,-36.5,39.166667,3.166666,-22.333333,8.5,-17,40.5,-40,20,-16.5,642,-634,-7.5,-3.5,23.666667,5.666666
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M11] rank=11 service=cartservice-1 metric=container_memory_failures.container.pgfault baseline=91.2 peak=1022.166667 signed_z=35.868 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:54.5,60.333333,-22.166666,-19.166667,-11,21.166667,14.666666,-68.833333,16.5,48,35,-15.833333,-24.833334,5.666667,22.5,-7.5,-12.5,27.5,-33,22,13,-36.5,258,-225.5,-41,5,22.5,-6.333333,33.166666,-82.333333,50.5,18,13.5,-31,-23.5,283.5,658.166667,-918.833334,7.666667,7.333333
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M12] rank=12 service=cartservice-1 metric=container_memory_failures.hierarchy.pgfault baseline=91.2 peak=1022.166667 signed_z=35.868 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:54.5,60.333333,-22.166666,-19.166667,-11,21.166667,14.666666,-68.833333,16.5,48,35,-15.833333,-24.833334,5.666667,22.5,-7.5,-12.5,27.5,-33,22,13,-36.5,258,-225.5,-41,5,22.5,-6.333333,33.166666,-82.333333,50.5,18,13.5,-31,-23.5,283.5,658.166667,-918.833334,7.666667,7.333333
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[2040.0,2220.0]

=== LOG SUMMARY ===
{"entries":[{"error_logs":27,"error_pct":0.2,"service":"recommendationservice-0","total_logs":13508},{"error_logs":12,"error_pct":0.09,"service":"recommendationservice-1","total_logs":13375},{"error_logs":9,"error_pct":0.07,"service":"recommendationservice-2","total_logs":13384},{"error_logs":1,"error_pct":0.0,"service":"frontend-0","total_logs":110118}],"mode":"errors","omitted_services":27,"service_count":31}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":43.5,"error_pct":0.0,"p95_during_ms":0.22389999999999938,"p95_pre_ms":0.156,"service":"paymentservice-1","spans":239},{"delta_pct":18.4,"error_pct":0.0,"p95_during_ms":0.09119999999999996,"p95_pre_ms":0.077,"service":"shippingservice-0","spans":1673},{"delta_pct":-15.5,"error_pct":0.0,"p95_during_ms":0.01775,"p95_pre_ms":0.021,"service":"adservice-1","spans":3565},{"delta_pct":10.2,"error_pct":0.0,"p95_during_ms":0.18299999999999997,"p95_pre_ms":0.166,"service":"paymentservice-2","spans":240},{"delta_pct":-9.2,"error_pct":0.0,"p95_during_ms":3.0005,"p95_pre_ms":3.303549999999999,"service":"recommendationservice-1","spans":8486},{"delta_pct":7.7,"error_pct":0.0,"p95_during_ms":0.26159999999999994,"p95_pre_ms":0.24279999999999996,"service":"emailservice-0","spans":240},{"delta_pct":-5.6,"error_pct":0.0,"p95_during_ms":2.9605,"p95_pre_ms":3.1346499999999993,"service":"recommendationservice-2","spans":8464},{"delta_pct":-3.1,"error_pct":0.0,"p95_during_ms":38.645849999999996,"p95_pre_ms":39.899649999999994,"service":"checkoutservice-0","spans":2826}],"omitted_services":32,"service_count":40}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=16 omitted_edges=0
[{"evidence_source":"metric","onset_rel_s":1260.0,"rank":1,"service":"cartservice2","severity_z":40.771},{"evidence_source":"metric","onset_rel_s":1320.0,"rank":2,"service":"cartservice","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1380.0,"rank":3,"service":"node-3","severity_z":38.005},{"evidence_source":"metric","onset_rel_s":1440.0,"rank":4,"service":"node-5","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1440.0,"rank":5,"service":"paymentservice","severity_z":177.586},{"evidence_source":"metric","onset_rel_s":1560.0,"rank":6,"service":"paymentservice2","severity_z":258.026},{"evidence_source":"metric","onset_rel_s":1560.0,"rank":7,"service":"shippingservice2","severity_z":62.416},{"evidence_source":"metric","onset_rel_s":1560.0,"rank":8,"service":"checkoutservice","severity_z":29.833},{"evidence_source":"metric","onset_rel_s":1620.0,"rank":9,"service":"adservice2","severity_z":35.862},{"evidence_source":"metric","onset_rel_s":1800.0,"rank":10,"service":"node-1","severity_z":29.608},{"evidence_source":"metric","onset_rel_s":1800.0,"rank":11,"service":"istio-ingressgateway","severity_z":26.384},{"evidence_source":"metric","onset_rel_s":1860.0,"rank":12,"service":"node-2","severity_z":31.958},{"evidence_source":"metric","onset_rel_s":2100.0,"rank":13,"service":"productcatalogservice","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":2280.0,"rank":14,"service":"node-6","severity_z":28.383}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"cartservice","caller":"checkoutservice"},{"callee":"paymentservice","caller":"checkoutservice"},{"callee":"productcatalogservice","caller":"checkoutservice"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

{"confidence":"high","reason":"Rank cartservice-0 first because cartservice-0 has metric evidence at propagation rank 2; although checkoutservice-0 is salient, the caller path checkoutservice -> cartservice means a disturbance in the callee can propagate back toward that caller-side symptom.","services":["cartservice-0","checkoutservice-0"]}

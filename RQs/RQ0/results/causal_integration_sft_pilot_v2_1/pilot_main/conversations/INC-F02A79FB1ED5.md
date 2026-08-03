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
opaque_id: INC-F02A79FB1ED5
observation_window={"duration_rel_s":2340.0,"source_metric_rows":40}
selection_summary={"candidate_count":63,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":1535,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["adservice","adservice-0","adservice-1","adservice-2","adservice-grpc","adservice-http","adservice2","adservice2-0","cartservice-0","cartservice-1","cartservice-2","cartservice-grpc","cartservice2-0","checkoutservice-0","checkoutservice-1","checkoutservice-2","checkoutservice-grpc","checkoutservice2-0","currencyservice-0","currencyservice-1","currencyservice-2","currencyservice-grpc","currencyservice2-0","emailservice-0","emailservice-1","emailservice-2","emailservice-grpc","emailservice2-0","frontend-0","frontend-1","frontend-2","frontend-http","frontend2-0","istio-egressgateway-7bfdcc9d86-g2d4q","istio-ingressgateway-565bffd4d-rn678","node-1","node-2","node-3","node-4","node-5","node-6","paymentservice-0","paymentservice-1","paymentservice-2","paymentservice-grpc","paymentservice2-0","productcatalogservice-0","productcatalogservice-1","productcatalogservice-2","productcatalogservice-grpc","productcatalogservice2-0","recommendationservice-0","recommendationservice-1","recommendationservice-2","recommendationservice-grpc","recommendationservice2-0","redis-cart-0","redis-cart2-0","shippingservice-0","shippingservice-1","shippingservice-2","shippingservice-grpc","shippingservice2-0"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[18.281,54.844,91.406,127.969,164.531,201.094,237.656,274.219,310.781,347.344,383.906,420.469,457.031,493.594,530.156,566.719,603.281,639.844,676.406,712.969,749.531,786.094,822.656,859.219,895.781,932.344,968.906,1005.469,1042.031,1078.594,1115.156,1151.719,1188.281,1224.844,1261.406,1297.969,1334.531,1371.094,1407.656,1444.219,1480.781,1517.344,1553.906,1590.469,1627.031,1663.594,1700.156,1736.719,1773.281,1809.844,1846.406,1882.969,1919.531,1956.094,1992.656,2029.219,2065.781,2102.344,2138.906,2175.469,2212.031,2248.594,2285.156,2321.719]
[M1] rank=1 service=node-1 metric=system.disk.pct_usage baseline=40.55 peak=40.56 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:40.55,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.01
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M2] rank=2 service=node-4 metric=system.disk.pct_usage baseline=52.95 peak=52.96 signed_z=999.0 onset_bin=62 onset_rel_s=2285.156 persistence_bins=2
values_compact=delta:52.95,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.01,-0.01,0,0,0.01,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M3] rank=3 service=productcatalogservice-0 metric=container_cpu_system_seconds baseline=0.0905 peak=20.385 signed_z=999.0 onset_bin=36 onset_rel_s=1334.531 persistence_bins=5
values_compact=delta:0.08,0,0.015,-0.015,0,0.015,0.005,-0.04,0.05,-0.035,0.025,-0.005,0.01,-0.03,0.035,-0.025,0.03,-0.02,0.01,-0.035,12.4,5.82,2.095,-2.34,1.01,-0.38,-11.47,-7.135,0.005,0.015,-0.015,0.035,-0.025,0.005,0.005,0,-0.005,-0.005,0.03,-0.045
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M4] rank=4 service=productcatalogservice-0 metric=container_fs_usage_MB./dev/vda1 baseline=0.15625 peak=1672.546875 signed_z=999.0 onset_bin=36 onset_rel_s=1334.531 persistence_bins=18
values_compact=delta:0.15625,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,22.3125,1650.078125,-286.992187,-163.765626,-372.722656,-242.339844,47.902344,-632.101562,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M5] rank=5 service=productcatalogservice-0 metric=container_memory_usage_MB baseline=23.646875 peak=255.966797 signed_z=999.0 onset_bin=36 onset_rel_s=1334.531 persistence_bins=18
values_compact=delta:23.515625,0.058594,-0.03125,-0.13086,0.083985,0.048828,0.082031,-0.011719,0.279297,-0.15039,0.083984,-0.458984,0.230468,0.013672,0.044922,0.019531,-0.015625,0.15625,0.105469,-0.103516,232.03711,-37.039063,37.107422,0.041016,-0.177735,0.138672,-183.505859,0.15625,-0.236328,0.273437,0.101563,-0.060547,-0.076172,-0.117187,0.082031,-0.042969,0.191406,-0.095703,0.220703,-0.296875
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M6] rank=6 service=productcatalogservice-0 metric=container_memory_failures.container.pgfault baseline=772.025 peak=114530.0 signed_z=902.819 onset_bin=36 onset_rel_s=1334.531 persistence_bins=5
values_compact=delta:871,-162,288,-274.5,52.5,-5.5,-42,-240.5,205,-90.5,362.5,-101,-102,-120.5,284.5,-288,254,-101,91.5,-146,73984,-35213,2489.5,-4984,2512.5,-144.5,75150,-113927,170,66.5,-113,149.5,-186,-60,115.5,-5.5,8.5,8,52.5,-146
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M7] rank=7 service=productcatalogservice-0 metric=container_memory_failures.hierarchy.pgfault baseline=772.025 peak=114530.0 signed_z=902.819 onset_bin=36 onset_rel_s=1334.531 persistence_bins=5
values_compact=delta:871,-162,288,-274.5,52.5,-5.5,-42,-240.5,205,-90.5,362.5,-101,-102,-120.5,284.5,-288,254,-101,91.5,-146,73984,-35213,2489.5,-4984,2512.5,-144.5,75150,-113927,170,66.5,-113,149.5,-186,-60,115.5,-5.5,8.5,8,52.5,-146
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M8] rank=8 service=productcatalogservice-0 metric=container_cpu_usage_seconds baseline=0.235298 peak=20.769226 signed_z=692.409 onset_bin=36 onset_rel_s=1334.531 persistence_bins=5
values_compact=delta:0.253789,-0.0291,0.041835,-0.039834,0.015494,-0.007289,0.020237,-0.081173,0.063059,-0.057693,0.101323,-0.029905,-0.011754,-0.041854,0.066833,-0.064251,0.086718,-0.055193,0.010969,-0.021544,13.152592,5.22657,2.169397,-2.423007,1.073752,-0.442187,-9.628108,-9.152995,0.045509,0.001658,-0.021277,0.042989,-0.047906,0.003174,0.003973,0.011617,-0.003447,-0.0101,0.029663,-0.041287
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M9] rank=9 service=productcatalogservice-0 metric=container_memory_working_set_MB baseline=22.142969 peak=97.744141 signed_z=507.064 onset_bin=36 onset_rel_s=1334.531 persistence_bins=18
values_compact=delta:22.011719,0.058593,-0.03125,-0.130859,0.083985,0.048828,0.082031,-0.011719,0.279297,-0.150391,0.083985,-0.458985,0.230469,0.013672,0.044922,0.019531,-0.015625,0.15625,0.105469,-0.103516,63.666016,2.398437,3.654297,2.619141,1.857422,1.232422,-25.69336,0.183594,-0.236328,0.273437,0.101563,-0.060547,-0.076172,-0.117187,0.082031,-0.042969,0.191406,-0.095703,0.220703,-0.296875
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M10] rank=10 service=adservice-2 metric=container_memory_failures.container.pgfault baseline=15.9 peak=3126.0 signed_z=477.264 onset_bin=36 onset_rel_s=1334.531 persistence_bins=5
values_compact=delta:10,2,0,-4,4,1.5,0.5,2.5,2,7.5,-10,-3.5,16.5,-8.5,-6,-4.5,0,2,21,-15,1888,723,497,-690,207,48.5,-1544,-1139.5,0,2,2,-2,-0.5,3,-2.5,-2,22.5,-20,-0.5,5.5
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M11] rank=11 service=adservice-2 metric=container_memory_failures.hierarchy.pgfault baseline=15.9 peak=3126.0 signed_z=477.264 onset_bin=36 onset_rel_s=1334.531 persistence_bins=5
values_compact=delta:10,2,0,-4,4,1.5,0.5,2.5,2,7.5,-10,-3.5,16.5,-8.5,-6,-4.5,0,2,21,-15,1888,723,497,-690,207,48.5,-1544,-1139.5,0,2,2,-2,-0.5,3,-2.5,-2,22.5,-20,-0.5,5.5
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M12] rank=12 service=adservice-1 metric=container_memory_failures.container.pgfault baseline=16.175 peak=2917.0 signed_z=425.252 onset_bin=36 onset_rel_s=1334.531 persistence_bins=5
values_compact=delta:8.5,5.5,-4,-2,4,0,4,2,-1,8.5,-7,-5,4.5,-9.5,7,-5,22.5,-21.5,15.5,-0.5,1863.5,750,55.5,8,213.5,-75.5,-1984,-849.5,0,0,6,-4,-2,8,-10,4,-4,8,-4,4
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[1140.0,1620.0]

=== LOG SUMMARY ===
{"entries":[{"error_logs":1196,"error_pct":8.77,"service":"adservice-0","total_logs":13642},{"error_logs":302,"error_pct":1.27,"service":"frontend-1","total_logs":23748},{"error_logs":296,"error_pct":1.27,"service":"frontend-2","total_logs":23326}],"mode":"errors","omitted_services":28,"service_count":31}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":-100.0,"error_pct":0.0,"p95_during_ms":0.0,"p95_pre_ms":203.0,"service":"cartservice-0","spans":2001},{"delta_pct":-100.0,"error_pct":0.0,"p95_during_ms":0.0,"p95_pre_ms":202.3499999999999,"service":"cartservice-1","spans":2006},{"delta_pct":-100.0,"error_pct":0.0,"p95_during_ms":0.0,"p95_pre_ms":203.0,"service":"cartservice-2","spans":1998},{"delta_pct":-77.3,"error_pct":0.0,"p95_during_ms":38.63285,"p95_pre_ms":169.90025000000003,"service":"checkoutservice-0","spans":474},{"delta_pct":-74.8,"error_pct":0.0,"p95_during_ms":38.339,"p95_pre_ms":152.027,"service":"checkoutservice-2","spans":470},{"delta_pct":-50.4,"error_pct":0.0,"p95_during_ms":40.568999999999996,"p95_pre_ms":81.80590000000018,"service":"checkoutservice-1","spans":466},{"delta_pct":42.5,"error_pct":0.0,"p95_during_ms":0.12029999999999985,"p95_pre_ms":0.08439999999999996,"service":"shippingservice-2","spans":283},{"delta_pct":19.8,"error_pct":0.0,"p95_during_ms":0.10300000000000001,"p95_pre_ms":0.08594999999999996,"service":"shippingservice-0","spans":280}],"omitted_services":31,"service_count":39}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=14 omitted_edges=0
[{"evidence_source":"metric","onset_rel_s":1200.0,"rank":1,"service":"productcatalogservice","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1200.0,"rank":2,"service":"adservice","severity_z":477.264},{"evidence_source":"metric","onset_rel_s":1260.0,"rank":3,"service":"cartservice","severity_z":139.117},{"evidence_source":"metric","onset_rel_s":1260.0,"rank":4,"service":"paymentservice2","severity_z":116.617},{"evidence_source":"metric","onset_rel_s":1260.0,"rank":5,"service":"node-5","severity_z":68.705},{"evidence_source":"metric","onset_rel_s":1380.0,"rank":6,"service":"currencyservice","severity_z":90.101},{"evidence_source":"metric","onset_rel_s":1440.0,"rank":7,"service":"paymentservice","severity_z":329.595},{"evidence_source":"metric","onset_rel_s":1500.0,"rank":8,"service":"checkoutservice","severity_z":94.482},{"evidence_source":"metric","onset_rel_s":1500.0,"rank":9,"service":"cartservice2","severity_z":31.671},{"evidence_source":"metric","onset_rel_s":1560.0,"rank":10,"service":"frontend","severity_z":119.876},{"evidence_source":"metric","onset_rel_s":1800.0,"rank":11,"service":"emailservice2","severity_z":342.921},{"evidence_source":"metric","onset_rel_s":1860.0,"rank":12,"service":"adservice2","severity_z":39.667},{"evidence_source":"metric","onset_rel_s":2040.0,"rank":13,"service":"node-4","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":2340.0,"rank":14,"service":"node-1","severity_z":999.0}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"cartservice","caller":"checkoutservice"},{"callee":"currencyservice","caller":"checkoutservice"},{"callee":"paymentservice","caller":"checkoutservice"},{"callee":"productcatalogservice","caller":"checkoutservice"},{"callee":"adservice","caller":"frontend"},{"callee":"cartservice","caller":"frontend"},{"callee":"checkoutservice","caller":"frontend"},{"callee":"currencyservice","caller":"frontend"},{"callee":"productcatalogservice","caller":"frontend"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

{"confidence":"high","reason":"Rank productcatalogservice-0 first because productcatalogservice-0 has direct container_cpu_system_seconds evidence (signed-z 999, persistence 5 bins); although checkoutservice-0 is salient, the caller path checkoutservice -> productcatalogservice means a disturbance in the callee can propagate back toward that caller-side symptom. The remaining entries preserve evidence-supported alternatives so the ranking retains calibrated uncertainty instead of collapsing to one answer.","services":["productcatalogservice-0","adservice-2","adservice-1","checkoutservice-0","cartservice-0"]}

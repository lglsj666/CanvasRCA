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
opaque_id: INC-977A8DFF966C
observation_window={"duration_rel_s":1440.0,"source_metric_rows":1441}
selection_summary={"candidate_count":17,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":263,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["adservice","cartservice","checkoutservice","currencyservice","emailservice","frontend","frontend-external","gke-gke-cluster-default-pool-2e1807ce-0e4z","gke-gke-cluster-default-pool-2e1807ce-cx8g","gke-gke-cluster-default-pool-2e1807ce-w819","gke-gke-cluster-default-pool-2e1807ce-xte3","loadgenerator","paymentservice","productcatalogservice","recommendationservice","redis","shippingservice"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[11.25,33.75,56.25,78.75,101.25,123.75,146.25,168.75,191.25,213.75,236.25,258.75,281.25,303.75,326.25,348.75,371.25,393.75,416.25,438.75,461.25,483.75,506.25,528.75,551.25,573.75,596.25,618.75,641.25,663.75,686.25,708.75,731.25,753.75,776.25,798.75,821.25,843.75,866.25,888.75,911.25,933.75,956.25,978.75,1001.25,1023.75,1046.25,1068.75,1091.25,1113.75,1136.25,1158.75,1181.25,1203.75,1226.25,1248.75,1271.25,1293.75,1316.25,1338.75,1361.25,1383.75,1406.25,1428.75]
[M1] rank=1 service=frontend metric=istio-error-total baseline=0.0 peak=0.667 signed_z=999.0 onset_bin=34 onset_rel_s=776.25 persistence_bins=4
values_compact=rle:0*34,0.667*1,0.333*1,0*13,0.4*1,0*3,0.133*1,0*10
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M2] rank=2 service=frontend-external metric=istio-error-total baseline=0.0 peak=0.6 signed_z=999.0 onset_bin=34 onset_rel_s=776.25 persistence_bins=4
values_compact=rle:0*34,0.6*1,0.4*1,0*13,0.333*1,0*3,0.133*1,0*10
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M3] rank=3 service=gke-gke-cluster-default-pool-2e1807ce-w819 metric=node-memory-active-bytes baseline=1713.619753 peak=11816595.911111 signed_z=999.0 onset_bin=53 onset_rel_s=1203.75 persistence_bins=2
values_compact=delta:2184.533333,91.022223,-273.066667,-728.177778,0,-455.111111,-91.022222,910.222222,182.044444,0,-273.066666,-91.022222,0,-364.088889,182.044444,728.177778,-182.044445,-728.177777,91.022222,273.066667,182.044444,91.022222,546.133334,182.044444,-546.133333,364.088889,0,91.022222,0,-1001.244445,364.088889,364.088889,-546.133333,1183.288889,273.066666,-1638.4,-91.022222,182.044445,-364.088889,182.044444,273.066667,91.022222,0,91.022222,455.111111,182.044445,-182.044445,91.022223,91.022222,-728.177778,-273.066667,91.022223,-91.022223,11815230.577778,-91.022222,-11814957.511111,91.022222,364.088889,182.044444,-273.066666,-182.044445,-273.066666,364.088888,273.066667
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M4] rank=4 service=checkoutservice metric=istio-latency-50 baseline=0.255481 peak=22.0 signed_z=568.856 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=raw:[0.234483,0.246591,0.291667,0.279412,0.226724,0.214706,0.228125,0.306818,0.322917,0.267857,0.213793,0.213793,0.241176,0.238971,0.279412,0.276316,0.23,0.288043,0.3,0.258333,0.229167,0.232143,0.224219,0.206818,0.2125,0.235577,0.257353,0.2375,0.25,0.265625,0.327381,0.354167,0.3625,0.603041,2.35,1.75,4.375,9.166667,5.0,2.916667,4.0625,5.357143,3.0,2.857143,2.96875,3.75,5.9375,3.958333,2.708333,2.916667,2.857143,3.75,7.1875,7.5,4.6875,6.5,14.285714,4.6875,2.416667,3.365385,2.727273,3.194444,8.125,22.0]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M5] rank=5 service=paymentservice metric=istio-latency-95 baseline=0.008489 peak=0.41875 signed_z=515.024 onset_bin=36 onset_rel_s=821.25 persistence_bins=10
values_compact=raw:[0.009078,0.008875,0.008975,0.009083,0.009107,0.009071,0.0085,0.008475,0.008806,0.008611,0.007,0.004969,0.007714,0.007786,0.008125,0.009139,0.009312,0.009089,0.009219,0.009213,0.009187,0.008944,0.008675,0.008125,0.008571,0.008789,0.0079,0.008,0.008464,0.008393,0.00805,0.008437,0.008357,0.007782,0.008875,0.0095,0.0048,0.046875,0.045417,0.0048,0.00675,0.00675,0.008875,0.009,0.007,0.00925,0.009545,0.009281,0.00625,0.009125,0.009333,0.009292,0.021437,0.022562,0.009556,0.009611,0.009639,0.009444,0.009187,0.009281,0.0055,0.35625,0.41875,0.023312]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M6] rank=6 service=checkoutservice metric=container-sockets baseline=9.0 peak=18.0 signed_z=500.0 onset_bin=53 onset_rel_s=1203.75 persistence_bins=11
values_compact=rle:9*53,18*11
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M7] rank=7 service=checkoutservice metric=istio-latency-90 baseline=0.661555 peak=51.0 signed_z=371.656 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=raw:[0.494737,0.6625,0.758333,0.641667,0.485937,0.466071,0.808333,0.9125,0.846429,0.791667,0.467857,0.469231,0.709091,0.685,0.925,0.875,0.46,0.498,0.708333,0.58,0.4975,0.691667,0.621429,0.4825,0.675,0.70625,0.57,0.5875,0.7625,0.7125,0.7375,0.78,0.83,3.547583,5.5,2.35,8.75,25.714286,23.714286,7.333333,8.7,9.071429,8.0,6.0,4.59375,8.125,19.5,18.5,6.25,6.5,4.857143,8.3,23.0,25.0,18.666667,21.333333,29.142857,26.857143,5.833333,6.166667,4.545455,14.666667,24.8,51.0]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M8] rank=8 service=paymentservice metric=istio-latency-90 baseline=0.007103 peak=0.3375 signed_z=301.078 onset_bin=37 onset_rel_s=843.75 persistence_bins=7
values_compact=raw:[0.008156,0.00775,0.00795,0.008167,0.008214,0.008143,0.007,0.00695,0.007611,0.007222,0.004927,0.00476,0.005429,0.005571,0.00625,0.007722,0.008208,0.008179,0.008438,0.008426,0.008375,0.007889,0.00735,0.00625,0.007143,0.007578,0.0058,0.006,0.006929,0.006786,0.0061,0.006875,0.006714,0.00562,0.00775,0.009,0.0046,0.04375,0.040833,0.0046,0.0049,0.0049,0.00775,0.008,0.004927,0.0085,0.009091,0.008563,0.004857,0.00825,0.008667,0.008583,0.017875,0.020125,0.009111,0.009222,0.009278,0.008889,0.008375,0.008563,0.004812,0.205,0.3375,0.021625]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M9] rank=9 service=paymentservice metric=istio-latency-99 baseline=0.010165 peak=0.48375 signed_z=252.264 onset_bin=15 onset_rel_s=348.75 persistence_bins=9
values_compact=raw:[0.009816,0.009775,0.009795,0.009817,0.009821,0.009814,0.0097,0.009695,0.009761,0.009722,0.0094,0.008825,0.009543,0.009557,0.009625,0.01735,0.0172,0.009818,0.009844,0.009843,0.009838,0.009789,0.009735,0.009625,0.009714,0.009758,0.00958,0.0096,0.009693,0.009679,0.00961,0.009687,0.009671,0.009556,0.009775,0.0099,0.00496,0.049375,0.049083,0.00496,0.00935,0.00935,0.009775,0.0098,0.0094,0.00985,0.009909,0.009856,0.00925,0.009825,0.009867,0.009858,0.024287,0.024512,0.009911,0.009922,0.009928,0.009889,0.009838,0.009856,0.0091,0.47125,0.48375,0.024663]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M10] rank=10 service=checkoutservice metric=istio-latency-95 baseline=0.875792 peak=55.5 signed_z=251.338 onset_bin=14 onset_rel_s=326.25 persistence_bins=33
values_compact=raw:[0.829167,0.95625,0.920833,0.820833,0.69375,0.591667,0.9875,1.225,0.923214,0.895833,0.6,0.616667,0.854545,0.8425,1.6375,1.5625,0.4925,0.9,0.9375,0.79,0.741667,0.845833,0.810714,0.70625,0.8375,0.853125,0.785,0.79375,0.88125,0.85625,0.99375,0.99,0.94,4.690458,7.75,2.425,9.375,27.857143,26.857143,8.666667,9.35,9.535714,9.0,8.0,4.796875,9.0625,24.75,24.25,8.125,8.25,6.5,9.15,26.5,27.5,24.333333,25.666667,40.5,29.857143,7.916667,8.083333,4.772727,22.333333,27.4,55.5]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M11] rank=11 service=checkoutservice metric=container-memory-failures-total baseline=2.626501 peak=184.082967 signed_z=142.531 onset_bin=33 onset_rel_s=753.75 persistence_bins=8
values_compact=raw:[5.242464,3.205192,4.043409,3.735541,2.405944,4.217488,4.176256,3.926541,3.098549,2.151019,1.361934,1.925629,3.057427,2.162968,1.730878,1.41169,1.41169,3.889111,3.602533,2.570022,3.34106,2.694006,3.937153,3.195008,2.788529,1.233752,0.729817,2.363841,3.08264,1.409113,1.069881,0.623705,1.071078,39.087035,25.924184,0.456135,0.959474,1.200667,1.382563,0.852457,0.135385,0.137501,0.267302,0.26409,0.182091,0.655872,0.977547,2.002202,1.911196,0.186802,0.382314,0.593784,0.618519,129.151468,123.803622,18.993792,11.733224,10.089376,8.351798,4.256601,2.947169,3.53453,5.841233,4.121903]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M12] rank=12 service=checkoutservice metric=istio-latency-99 baseline=1.369375 peak=59.1 signed_z=102.054 onset_bin=33 onset_rel_s=753.75 persistence_bins=30
values_compact=raw:[1.6,2.1475,1.915,0.964167,0.93875,0.918333,2.1775,2.245,0.984643,0.979167,0.92,0.923333,0.970909,0.9685,2.3275,2.3125,0.87,2.1025,2.0875,0.958,0.948333,0.969167,0.962143,0.94125,0.9675,0.970625,0.957,0.95875,0.97625,0.97125,2.1925,2.185,1.84,8.62855,9.55,2.485,9.875,29.571429,29.371429,9.733333,9.87,9.907143,9.8,9.6,4.959375,9.8125,28.95,28.85,9.625,9.65,9.3,9.83,29.3,29.5,28.866667,29.133333,56.1,53.7,9.583333,9.616667,4.954545,28.466667,29.48,59.1]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[734.0,826.0]

=== LOG SUMMARY ===
{"entries":[{"error_logs":29,"error_pct":0.05,"service":"frontend","total_logs":60258},{"error_logs":7,"error_pct":0.37,"service":"checkoutservice","total_logs":1872}],"mode":"errors","omitted_services":8,"service_count":10}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":517.2,"error_pct":0.0,"p95_during_ms":9125.679800000024,"p95_pre_ms":1478.6365999999998,"service":"checkoutservice","spans":8518},{"delta_pct":117.3,"error_pct":0.0,"p95_during_ms":0.9249499999999988,"p95_pre_ms":0.42560000000000037,"service":"emailservice","spans":1196},{"delta_pct":-45.3,"error_pct":0.0,"p95_during_ms":0.2189,"p95_pre_ms":0.40019999999999983,"service":"paymentservice","spans":908},{"delta_pct":-6.0,"error_pct":0.0,"p95_during_ms":4.644,"p95_pre_ms":4.93975,"service":"recommendationservice","spans":26078},{"delta_pct":4.2,"error_pct":0.0,"p95_during_ms":0.025,"p95_pre_ms":0.024,"service":"productcatalogservice","spans":98112},{"delta_pct":3.7,"error_pct":0.0,"p95_during_ms":0.18979999999999972,"p95_pre_ms":0.183,"service":"currencyservice","spans":54218},{"delta_pct":-0.5,"error_pct":0.0,"p95_during_ms":191.7865,"p95_pre_ms":192.6549999999998,"service":"frontend","spans":196763}],"omitted_services":0,"service_count":7}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=3 omitted_edges=0
[{"evidence_source":"metric","onset_rel_s":720.0,"rank":1,"service":"adservice","severity_z":12.755},{"evidence_source":"trace","onset_rel_s":735.0,"rank":2,"service":"checkoutservice","severity_z":594.953},{"evidence_source":"metric","onset_rel_s":771.0,"rank":3,"service":"frontend-external","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":772.8,"rank":4,"service":"frontend","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":993.0,"rank":5,"service":"cartservice","severity_z":21.995},{"evidence_source":"metric","onset_rel_s":1201.2,"rank":6,"service":"gke-gke-cluster-default-pool-2e1807ce-w819","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1204.8,"rank":7,"service":"shippingservice","severity_z":87.901},{"evidence_source":"trace","onset_rel_s":1245.0,"rank":8,"service":"emailservice","severity_z":5.69},{"evidence_source":"metric","onset_rel_s":1372.2,"rank":9,"service":"paymentservice","severity_z":515.024},{"evidence_source":"none","onset_rel_s":null,"rank":10,"service":"productcatalogservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":11,"service":"gke-gke-cluster-default-pool-2e1807ce-0e4z","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":12,"service":"gke-gke-cluster-default-pool-2e1807ce-xte3","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":13,"service":"redis","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":14,"service":"gke-gke-cluster-default-pool-2e1807ce-cx8g","severity_z":0.0}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"emailservice","caller":"checkoutservice"},{"callee":"paymentservice","caller":"checkoutservice"},{"callee":"productcatalogservice","caller":"checkoutservice"},{"callee":"checkoutservice","caller":"frontend"},{"callee":"productcatalogservice","caller":"frontend"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

{"confidence":"high","reason":"Rank checkoutservice first because checkoutservice has direct istio-latency-50 evidence (signed-z 568.86, persistence 31 bins); although frontend is salient, the caller path frontend -> checkoutservice means a disturbance in the callee can propagate back toward that caller-side symptom.","services":["checkoutservice","frontend"]}

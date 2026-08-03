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
opaque_id: INC-DDFBAFE8DB5E
observation_window={"duration_rel_s":1440.0,"source_metric_rows":1441}
selection_summary={"candidate_count":16,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":259,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["adservice","cartservice","checkoutservice","currencyservice","emailservice","frontend","frontend-external","gke-gke-cluster-default-pool-2e1807ce-0e4z","gke-gke-cluster-default-pool-2e1807ce-cx8g","gke-gke-cluster-default-pool-2e1807ce-w819","loadgenerator","paymentservice","productcatalogservice","recommendationservice","redis","shippingservice"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[11.25,33.75,56.25,78.75,101.25,123.75,146.25,168.75,191.25,213.75,236.25,258.75,281.25,303.75,326.25,348.75,371.25,393.75,416.25,438.75,461.25,483.75,506.25,528.75,551.25,573.75,596.25,618.75,641.25,663.75,686.25,708.75,731.25,753.75,776.25,798.75,821.25,843.75,866.25,888.75,911.25,933.75,956.25,978.75,1001.25,1023.75,1046.25,1068.75,1091.25,1113.75,1136.25,1158.75,1181.25,1203.75,1226.25,1248.75,1271.25,1293.75,1316.25,1338.75,1361.25,1383.75,1406.25,1428.75]
[M1] rank=1 service=emailservice metric=container-memory-failures-total baseline=0.171284 peak=757.986417 signed_z=999.0 onset_bin=32 onset_rel_s=731.25 persistence_bins=13
values_compact=raw:[0.0,0.0,0.087308,0.109706,0.618071,0.628209,0.0,0.0,0.0,0.0,0.040899,0.087635,0.180865,0.227638,0.096196,0.041365,0.597833,0.524078,0.170518,0.0,0.091794,0.085301,0.0,0.0,0.0,0.0,0.190585,0.842773,0.658127,0.042145,0.0,0.047208,37.012835,47.974536,529.312925,406.035998,1.263472,0.259051,0.119227,0.083852,0.04561,0.039819,0.18648,0.187187,0.0,0.170849,0.499329,0.582756,0.266099,0.0,0.0,432.751279,459.807215,0.319584,0.203876,514.460319,561.433333,1.565898,0.494573,522.394785,431.842889,1.002104,0.705849,0.237921]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,20,22,23,22,21,17,23,22,23,22,23,22,23,22,23,22,23,23
[M2] rank=2 service=emailservice metric=container-memory-rss baseline=40642389.333333 peak=162246656.0 signed_z=999.0 onset_bin=33 onset_rel_s=753.75 persistence_bins=29
values_compact=delta:40624128,0,8192,0,-8192,0,0,0,0,0,4096,4096,12288,8192,0,0,-20480,16384,0,0,8192,0,0,0,0,0,-53248,53248,4096,0,0,4096,4096,1802240,38682624,110592,16384,8192,4096,4096,0,0,16384,0,0,-40652800,0,-69632,0,0,2199552,38350848,28672,0,16384,40386560,0,147456,2195456,38223872,45056,36864,-40566784,0
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M3] rank=3 service=emailservice metric=container-memory-usage-bytes baseline=43214205.155556 peak=172412928.0 signed_z=999.0 onset_bin=33 onset_rel_s=753.75 persistence_bins=29
values_compact=delta:43192320,4096,8192,4096,-12288,-2048,2048,-4096,4096,0,0,4096,16384,8192,0,-4096,-12288,12288,4096,-4096,4096,8192,-4096,0,-4096,4096,-49152,49152,4096,-4096,0,8192,4096,2318336,40718336,110592,16384,8192,4096,4096,4096,-4096,16384,-4096,4096,-43220992,0,-73728,0,0,2756608,40337408,20480,-4096,16384,42930176,0,147456,2707456,40247296,49152,36864,-43118592,-4096
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M4] rank=4 service=emailservice metric=container-memory-working-set-bytes baseline=43140477.155556 peak=172118016.0 signed_z=999.0 onset_bin=33 onset_rel_s=753.75 persistence_bins=29
values_compact=delta:43118592,4096,8192,4096,-12288,-2048,2048,-4096,4096,0,0,4096,16384,8192,0,-4096,-12288,12288,4096,-4096,4096,8192,-4096,0,-4096,4096,-49152,49152,4096,-4096,0,8192,4096,2318336,40644608,110592,16384,8192,4096,4096,4096,-4096,16384,-4096,4096,-43147264,0,-73728,0,0,2756608,40263680,20480,-4096,16384,42856448,0,147456,2707456,40173568,49152,36864,-43044864,-4096
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M5] rank=5 service=emailservice metric=istio-latency-50 baseline=0.003022 peak=0.110714 signed_z=999.0 onset_bin=33 onset_rel_s=753.75 persistence_bins=30
values_compact=delta:0.003036,0.000002,0.000035,-0.00004,-0.000033,0,0,0,0,0,0,0,0.0001,0.000005,-0.000105,0,0,0,0,0,0.000103,0,-0.000103,0,0,0,0,0,0.000054,-0.000018,-0.000036,0,0,0.000148,0.000252,0.000337,-0.000192,-0.00015,-0.000058,0.000538,0.000118,-0.000084,-0.000491,-0.00024,-0.000065,0.000061,-0.000016,0.000437,0.000037,0.000064,-0.000038,0.000009,-0.000307,-0.000062,0.000152,-0.000189,0.000494,0.000881,-0.000493,-0.000345,0.000002,-0.000646,0.000083,0.000348
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M6] rank=6 service=emailservice metric=istio-latency-90 baseline=0.004639 peak=1.26268 signed_z=999.0 onset_bin=33 onset_rel_s=753.75 persistence_bins=30
values_compact=delta:0.004665,0.000004,0.000062,-0.000071,-0.00006,0,0,0,0,0,0,0,0.00018,0.000009,-0.000189,0,0,0,0,0,0.000185,0,-0.000185,0,0,0,0,0,0.000097,-0.000033,-0.000064,0,0,0.000267,0.110133,0.087,-0.012,0.0045,0.013,0.0365,0.09526,0.244073,-0.335833,-0.24258,-0.000117,0.00011,-0.000029,0.341141,0.028975,-0.1775,-0.005455,0.037955,-0.037,-0.078,0.105,-0.09,0.76503,-0.058665,-0.591365,0.001113,-0.003187,-0.238049,0.103327,0.105462
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M7] rank=7 service=emailservice metric=istio-latency-95 baseline=0.00485 peak=2.7189 signed_z=999.0 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=delta:0.004869,0.000004,0.000065,-0.000075,-0.000063,0,0,0,0,0,0,0,0.00019,0.00001,-0.0002,0,0,0,0,0,0.000195,0,-0.000195,0,0,0,0,0,0.000103,-0.000035,-0.000068,0,0,0.13645,0.04125,0.057742,-0.010867,0.0925,0.125,0.028125,0.11426,0.30057,0.59767,-1.27125,-0.0975,0.05625,-0.0275,0.525513,0.014487,-0.45125,-0.008409,0.472159,-0.0233,-0.4442,0.5925,-0.5975,2.0475,-0.265905,-1.534095,1.236135,-0.031875,-1.53426,0.034102,0.151638
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M8] rank=8 service=emailservice metric=istio-latency-99 baseline=0.005976 peak=4.54378 signed_z=999.0 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=delta:0.0072,0.00015,0.001225,-0.001625,-0.00199,0,0,0,0,0,0,0,0.00399,0.00005,-0.00404,0,0,0,0,0,0.004015,0,-0.004015,0,0,0,0,0,0.00314,-0.00095,-0.00219,0,0,0.22329,0.00825,0.6335,-0.08,-0.0325,3.03,0.6375,-3.507148,1.083842,0.295806,-0.165,-1.33,-0.0525,-0.5205,0.705103,0.002897,-0.515,-0.05375,1.74125,-0.00699,-0.30801,0.195,-1.12,3.555,-0.088635,-3.446365,1.452227,-0.006375,-2.106852,0.00682,1.761068
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M9] rank=9 service=gke-gke-cluster-default-pool-2e1807ce-cx8g metric=node-memory-active-bytes baseline=8942.554074 peak=64809551.644444 signed_z=999.0 onset_bin=37 onset_rel_s=843.75 persistence_bins=4
values_compact=delta:9648.355556,-2093.511112,-637.155555,1638.4,-1547.377778,455.111111,1183.288889,1820.444445,0,-2002.488889,910.222222,182.044444,182.044445,1638.4,-1911.466667,-1274.311111,728.177778,-1183.288889,728.177778,1001.244444,-910.222222,182.044444,1183.288889,-182.044444,-1729.422222,-1092.266667,1365.333333,2002.488889,-455.111111,-182.044444,-273.066667,0,1092.266667,-1365.333334,-364.088889,-1183.288889,-273.066666,32458433.422222,546.133333,-114141.866666,-637.155556,-32342744.177778,91.022223,637.155555,91.022222,-1547.377777,-1092.266667,-819.2,1547.377778,1911.466666,-1547.377777,1092.266666,-182.044444,-910.222222,819.2,-3276.8,1001.244444,2457.6,-1456.355556,1365.333334,455.111111,-1911.466667,273.066667,455.111111
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M10] rank=10 service=checkoutservice metric=istio-latency-95 baseline=0.237593 peak=3.3125 signed_z=258.775 onset_bin=33 onset_rel_s=753.75 persistence_bins=30
values_compact=raw:[0.246786,0.237045,0.2325,0.243864,0.243625,0.21925,0.230962,0.237143,0.238333,0.2325,0.231667,0.2395,0.23925,0.233977,0.232917,0.235326,0.233235,0.232,0.234687,0.238333,0.238125,0.238,0.23875,0.236154,0.231053,0.2275,0.235417,0.30625,0.26875,0.233929,0.2335,0.235,0.237143,0.415625,0.5,0.6125,0.484821,0.853125,0.965625,0.493056,0.783333,0.98125,1.9625,1.58125,0.45625,0.48,0.420833,0.833333,0.783333,0.467188,0.6,1.3375,1.4125,0.875,0.96875,0.6125,3.3125,2.1625,0.494792,1.525,1.525,0.325,0.245,1.0]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M11] rank=11 service=emailservice metric=container-sockets baseline=3.0 peak=13.0 signed_z=218.489 onset_bin=34 onset_rel_s=776.25 persistence_bins=24
values_compact=rle:3*34,6*11,3*6,6*4,8*2,10*2,13*3,10*2
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M12] rank=12 service=emailservice metric=container-memory-cache baseline=73728.0 peak=294912.0 signed_z=208.876 onset_bin=34 onset_rel_s=776.25 persistence_bins=24
values_compact=rle:73728*34,147456*11,73728*6,147456*4,221184*4,294912*3,221184*2
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[1129.0,1440.0]

=== LOG SUMMARY ===
{"entries":[{"error_logs":10,"error_pct":0.49,"service":"checkoutservice","total_logs":2045},{"error_logs":1,"error_pct":0.15,"service":"emailservice","total_logs":685}],"mode":"errors","omitted_services":8,"service_count":10}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":39.6,"error_pct":0.0,"p95_during_ms":135.07225,"p95_pre_ms":96.77529999999992,"service":"checkoutservice","spans":9283},{"delta_pct":-2.9,"error_pct":0.0,"p95_during_ms":0.236,"p95_pre_ms":0.243,"service":"currencyservice","spans":56544},{"delta_pct":-2.9,"error_pct":0.0,"p95_during_ms":61.612999999999914,"p95_pre_ms":63.474,"service":"frontend","spans":205485},{"delta_pct":-1.9,"error_pct":0.0,"p95_during_ms":0.479,"p95_pre_ms":0.4885,"service":"emailservice","spans":1162},{"delta_pct":0.8,"error_pct":0.0,"p95_during_ms":0.38469999999999943,"p95_pre_ms":0.38154999999999994,"service":"paymentservice","spans":970},{"delta_pct":0.8,"error_pct":0.0,"p95_during_ms":5.361499999999999,"p95_pre_ms":5.317649999999998,"service":"recommendationservice","spans":27322},{"delta_pct":0.0,"error_pct":0.0,"p95_during_ms":0.028,"p95_pre_ms":0.028,"service":"productcatalogservice","spans":102165}],"omitted_services":0,"service_count":7}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=2 omitted_edges=0
[{"evidence_source":"metric","onset_rel_s":762.0,"rank":1,"service":"emailservice","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":837.0,"rank":2,"service":"gke-gke-cluster-default-pool-2e1807ce-cx8g","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":853.8,"rank":3,"service":"recommendationservice","severity_z":22.96},{"evidence_source":"metric","onset_rel_s":865.2,"rank":4,"service":"shippingservice","severity_z":21.98},{"evidence_source":"metric","onset_rel_s":1093.8,"rank":5,"service":"adservice","severity_z":56.807},{"evidence_source":"metric","onset_rel_s":1282.2,"rank":6,"service":"cartservice","severity_z":17.514},{"evidence_source":"metric","onset_rel_s":1338.0,"rank":7,"service":"paymentservice","severity_z":10.511},{"evidence_source":"trace","onset_rel_s":1425.0,"rank":8,"service":"checkoutservice","severity_z":3.803},{"evidence_source":"none","onset_rel_s":null,"rank":9,"service":"gke-gke-cluster-default-pool-2e1807ce-0e4z","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":10,"service":"frontend","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":11,"service":"gke-gke-cluster-default-pool-2e1807ce-w819","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":12,"service":"productcatalogservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":13,"service":"loadgenerator","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":14,"service":"frontend-external","severity_z":0.0}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"emailservice","caller":"checkoutservice"},{"callee":"paymentservice","caller":"checkoutservice"},{"callee":"productcatalogservice","caller":"checkoutservice"},{"callee":"checkoutservice","caller":"frontend"},{"callee":"productcatalogservice","caller":"frontend"},{"callee":"recommendationservice","caller":"frontend"},{"callee":"productcatalogservice","caller":"recommendationservice"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

{"confidence":"high","reason":"Rank emailservice first because emailservice has direct container-memory-failures-total evidence (signed-z 999, persistence 13 bins); although checkoutservice is salient, the caller path checkoutservice -> emailservice means a disturbance in the callee can propagate back toward that caller-side symptom.","services":["emailservice","checkoutservice"]}

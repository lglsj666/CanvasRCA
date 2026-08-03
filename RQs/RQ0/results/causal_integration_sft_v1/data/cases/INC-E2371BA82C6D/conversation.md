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
opaque_id: INC-E2371BA82C6D
observation_window={"duration_rel_s":1440.0,"source_metric_rows":1441}
selection_summary={"candidate_count":18,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":267,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["adservice","cartservice","checkoutservice","currencyservice","emailservice","frontend","frontend-external","gke-gke-cluster-default-pool-2e1807ce-0e4z","gke-gke-cluster-default-pool-2e1807ce-cx8g","gke-gke-cluster-default-pool-2e1807ce-w819","gke-gke-cluster-default-pool-2e1807ce-xte3","istio-init","loadgenerator","paymentservice","productcatalogservice","recommendationservice","redis","shippingservice"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[11.25,33.75,56.25,78.75,101.25,123.75,146.25,168.75,191.25,213.75,236.25,258.75,281.25,303.75,326.25,348.75,371.25,393.75,416.25,438.75,461.25,483.75,506.25,528.75,551.25,573.75,596.25,618.75,641.25,663.75,686.25,708.75,731.25,753.75,776.25,798.75,821.25,843.75,866.25,888.75,911.25,933.75,956.25,978.75,1001.25,1023.75,1046.25,1068.75,1091.25,1113.75,1136.25,1158.75,1181.25,1203.75,1226.25,1248.75,1271.25,1293.75,1316.25,1338.75,1361.25,1383.75,1406.25,1428.75]
[M1] rank=1 service=gke-gke-cluster-default-pool-2e1807ce-0e4z metric=node-memory-active-bytes baseline=44128.45183 peak=47370148.977778 signed_z=999.0 onset_bin=53 onset_rel_s=1203.75 persistence_bins=2
values_compact=delta:141812.622222,-48059.733333,-6098.488889,182.044444,-18113.422222,3185.777778,-2093.511111,-10194.488889,1547.377778,-4096,-15018.666667,1092.266667,-1001.244445,182.044445,-4004.977778,-4096,2821.688889,-273.066667,-2639.644444,-3551.972174,-6733.538937,2095.307402,180.248153,-3549.866666,-6553.6,-273.066667,1456.355555,-2366.577777,-2275.555556,1456.355556,728.177777,-455.111111,-637.155555,-910.222222,-2366.577778,-2002.488889,-1911.466667,2730.666667,-273.066667,-2184.533333,-1001.244445,-1456.355555,3367.822222,-91.022222,-1729.422222,2275.555555,-182.044444,-3003.733334,-2457.6,2093.017613,-363.59539,-818.811604,636.767159,47363959.466667,0,-47364505.6,637.155555,-455.111111,-1001.244444,-637.155556,-728.177777,2275.555555,-819.2,-1001.244444
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M2] rank=2 service=checkoutservice metric=container-cpu-system-seconds-total baseline=0.136689 peak=15.386135 signed_z=465.953 onset_bin=32 onset_rel_s=731.25 persistence_bins=11
values_compact=raw:[0.094737,0.101365,0.152556,0.165335,0.127658,0.147649,0.149961,0.104286,0.068319,0.086554,0.116379,0.148684,0.134508,0.173812,0.16707,0.156911,0.176902,0.140063,0.107214,0.157985,0.12418,0.084108,0.133741,0.09352,0.179834,0.161174,0.102331,0.126687,0.148752,0.188737,0.173227,0.119082,1.90942,8.143048,13.936659,15.138295,14.922013,14.735036,13.923524,12.788549,11.975542,8.767611,2.86356,0.108225,0.108589,0.171721,0.16368,0.112918,0.120823,0.173444,0.169465,0.130589,0.170034,0.154941,0.14944,0.136184,0.10816,0.134772,0.14587,0.129963,0.123549,0.121033,0.14977,0.150881]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M3] rank=3 service=checkoutservice metric=container-cpu-usage-seconds-total baseline=0.393426 peak=19.601395 signed_z=254.843 onset_bin=32 onset_rel_s=731.25 persistence_bins=11
values_compact=raw:[0.245747,0.241003,0.4246,0.463124,0.326138,0.418137,0.427128,0.349284,0.341234,0.32978,0.390858,0.455326,0.392416,0.516663,0.51997,0.431827,0.449197,0.387665,0.333698,0.441759,0.360377,0.277348,0.38137,0.290627,0.473546,0.412706,0.332308,0.384914,0.45029,0.523282,0.425614,0.339432,2.578264,10.498068,17.734938,19.409053,19.217234,18.736266,17.848265,16.631452,15.615851,11.476469,3.876235,0.264261,0.300362,0.516382,0.510636,0.350361,0.333493,0.469614,0.444375,0.344753,0.436902,0.402934,0.339881,0.330613,0.312964,0.395354,0.382852,0.305864,0.331211,0.419082,0.46576,0.361509]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M4] rank=4 service=checkoutservice metric=container-memory-mapped-file baseline=0.0 peak=2215936.0 signed_z=106.506 onset_bin=32 onset_rel_s=731.25 persistence_bins=32
values_compact=rle:0*32,2215936*32
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M5] rank=5 service=checkoutservice metric=container-cpu-user-seconds-total baseline=0.256737 peak=4.379295 signed_z=82.61 onset_bin=32 onset_rel_s=731.25 persistence_bins=11
values_compact=raw:[0.151008,0.139638,0.272047,0.297788,0.206888,0.270488,0.272823,0.245001,0.265703,0.243224,0.271966,0.306642,0.255637,0.352502,0.3529,0.274917,0.272297,0.254076,0.229186,0.283776,0.236199,0.193648,0.247631,0.197103,0.29371,0.251532,0.229977,0.258228,0.301538,0.329072,0.252387,0.22035,0.668841,2.35502,3.79828,4.271337,4.290714,4.001233,3.924743,3.816377,3.640307,2.708858,1.012675,0.156036,0.191774,0.344659,0.344659,0.236682,0.217104,0.291749,0.274908,0.201923,0.266869,0.247991,0.190441,0.186413,0.201808,0.252011,0.229623,0.175901,0.20766,0.298049,0.336746,0.212321]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M6] rank=6 service=checkoutservice metric=container-memory-cache baseline=0.0 peak=2215936.0 signed_z=55.476 onset_bin=32 onset_rel_s=731.25 persistence_bins=32
values_compact=rle:0*32,2215936*32
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M7] rank=7 service=checkoutservice metric=istio-latency-90 baseline=0.22858 peak=0.840909 signed_z=32.368 onset_bin=33 onset_rel_s=753.75 persistence_bins=10
values_compact=raw:[0.228826,0.223953,0.220652,0.2185,0.214375,0.226429,0.227969,0.235,0.30625,0.24,0.22,0.224615,0.2254,0.220536,0.211667,0.2155,0.222885,0.221429,0.22075,0.224444,0.23,0.236071,0.222368,0.212059,0.221957,0.231429,0.233333,0.237308,0.237222,0.225,0.2206,0.226,0.239444,0.54,0.84,0.75,0.480952,0.55,0.5,0.461765,0.455952,0.430263,0.391667,0.22,0.22375,0.243333,0.2392,0.210769,0.219062,0.236731,0.2344,0.22,0.225769,0.236429,0.232857,0.216786,0.215385,0.218421,0.222857,0.223529,0.222647,0.223158,0.231053,0.228437]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M8] rank=8 service=checkoutservice metric=container-sockets baseline=9.0 peak=23.0 signed_z=31.705 onset_bin=32 onset_rel_s=731.25 persistence_bins=32
values_compact=rle:9*32,22*3,22.5*1,22*1,23*1,22*26
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M9] rank=9 service=checkoutservice metric=container-memory-failures-total baseline=5.550174 peak=104.308501 signed_z=27.67 onset_bin=32 onset_rel_s=731.25 persistence_bins=2
values_compact=raw:[12.853036,9.045309,12.633837,14.74604,9.002475,7.829836,6.983601,4.992624,2.994366,3.038974,5.366474,6.010054,1.271948,3.432731,3.432731,2.311587,3.254797,2.625862,1.747807,3.166489,5.180534,4.72427,4.72427,0.866667,5.889036,2.550592,1.647277,5.081712,9.13017,8.792191,6.439991,3.7766,89.104089,99.133917,3.718404,3.702323,1.210252,1.30867,1.996709,0.491093,0.47894,4.884063,5.221298,2.923502,3.056367,3.646571,4.537227,5.120702,2.377448,2.299079,1.867073,1.630118,6.566276,5.875811,0.918625,3.456423,3.491544,1.829791,3.858803,4.333694,2.244194,6.642564,9.07376,2.043441]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M10] rank=10 service=checkoutservice metric=container-memory-usage-bytes baseline=9959099.733333 peak=21483520.0 signed_z=24.614 onset_bin=0 onset_rel_s=11.25 persistence_bins=34
values_compact=delta:8286208,237568,1011712,249856,94208,-225280,405504,12288,270336,-630784,376832,57344,49152,-401408,49152,188416,114688,94208,-262144,135168,233472,-462848,311296,-323584,462848,-196608,28672,176128,-118784,-110592,294912,16384,7704576,892928,-471040,192512,8192,1347584,-421888,1478656,24576,-299008,122880,122880,122880,-348160,204800,245760,102400,-323584,-2117632,57344,-2396160,0,73728,0,-1921024,-552960,237568,-225280,65536,684032,-335872,-274432
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M11] rank=11 service=checkoutservice metric=container-memory-working-set-bytes baseline=9959099.733333 peak=21483520.0 signed_z=24.614 onset_bin=0 onset_rel_s=11.25 persistence_bins=34
values_compact=delta:8286208,237568,1011712,249856,94208,-225280,405504,12288,270336,-630784,376832,57344,49152,-401408,49152,188416,114688,94208,-262144,135168,233472,-462848,311296,-323584,462848,-196608,28672,176128,-118784,-110592,294912,16384,7704576,892928,-471040,192512,8192,1347584,-421888,1478656,24576,-299008,122880,122880,122880,-348160,204800,245760,102400,-323584,-2117632,57344,-2396160,0,73728,0,-1921024,-552960,237568,-225280,65536,684032,-335872,-274432
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M12] rank=12 service=adservice metric=istio-bytes-90 baseline=0.249702 peak=1.025299 signed_z=22.448 onset_bin=31 onset_rel_s=708.75 persistence_bins=8
values_compact=raw:[0.24589,0.244575,0.24402,0.244381,0.244471,0.244156,0.244116,0.244712,0.244369,0.244286,0.244247,0.244266,0.244527,0.244161,0.244381,0.244677,0.2443,0.244375,0.244338,0.244111,0.244254,0.244344,0.244612,0.244431,0.244355,0.245103,0.247534,0.303571,0.249066,0.246174,0.247893,0.37375,0.388462,0.285714,0.249143,0.249733,0.249263,0.24989,0.266667,0.268149,0.314259,0.421063,0.432936,0.42875,0.435106,0.421429,0.38125,0.313333,0.249789,0.248411,0.249082,0.249075,0.254167,0.280769,0.249158,0.249888,0.249888,0.2625,0.270833,0.25,0.303846,0.2875,0.249164,0.247535]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[720.0,973.0]

=== LOG SUMMARY ===
{"entries":[{"change_pct":-81.7,"n_during":294,"n_pre":1608,"service":"checkoutservice"},{"change_pct":-81.7,"n_during":98,"n_pre":536,"service":"emailservice"},{"change_pct":-81.7,"n_during":196,"n_pre":1072,"service":"paymentservice"},{"change_pct":-79.0,"n_during":2315,"n_pre":11022,"service":"recommendationservice"},{"change_pct":-78.9,"n_during":1834,"n_pre":8708,"service":"shippingservice"},{"change_pct":-78.8,"n_during":1876,"n_pre":8864,"service":"adservice"},{"change_pct":-78.7,"n_during":3209,"n_pre":15093,"service":"cartservice"},{"change_pct":-78.6,"n_during":11254,"n_pre":52505,"service":"frontend"}],"mode":"volume","omitted_services":2,"service_count":10}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":96.1,"error_pct":0.0,"p95_during_ms":155.6415,"p95_pre_ms":79.38179999999998,"service":"checkoutservice","spans":8814},{"delta_pct":-17.0,"error_pct":0.0,"p95_during_ms":0.36569999999999975,"p95_pre_ms":0.44054999999999994,"service":"emailservice","spans":1210},{"delta_pct":-6.3,"error_pct":0.0,"p95_during_ms":0.7097999999999988,"p95_pre_ms":0.7573999999999992,"service":"paymentservice","spans":922},{"delta_pct":-4.2,"error_pct":0.0,"p95_during_ms":0.25,"p95_pre_ms":0.261,"service":"currencyservice","spans":57153},{"delta_pct":2.4,"error_pct":0.0,"p95_during_ms":71.10619999999999,"p95_pre_ms":69.44934999999994,"service":"frontend","spans":206549},{"delta_pct":1.1,"error_pct":0.0,"p95_during_ms":4.624299999999997,"p95_pre_ms":4.575,"service":"recommendationservice","spans":27250},{"delta_pct":0.0,"error_pct":0.0,"p95_during_ms":0.025,"p95_pre_ms":0.025,"service":"productcatalogservice","spans":102391}],"omitted_services":0,"service_count":7}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=3 omitted_edges=0
[{"evidence_source":"trace","onset_rel_s":735.0,"rank":1,"service":"checkoutservice","severity_z":23.027},{"evidence_source":"metric","onset_rel_s":1192.2,"rank":2,"service":"gke-gke-cluster-default-pool-2e1807ce-0e4z","severity_z":999.0},{"evidence_source":"none","onset_rel_s":null,"rank":3,"service":"adservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":4,"service":"productcatalogservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":5,"service":"shippingservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":6,"service":"emailservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":7,"service":"paymentservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":8,"service":"recommendationservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":9,"service":"cartservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":10,"service":"frontend-external","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":11,"service":"gke-gke-cluster-default-pool-2e1807ce-xte3","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":12,"service":"frontend","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":13,"service":"gke-gke-cluster-default-pool-2e1807ce-cx8g","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":14,"service":"gke-gke-cluster-default-pool-2e1807ce-w819","severity_z":0.0}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"emailservice","caller":"checkoutservice"},{"callee":"paymentservice","caller":"checkoutservice"},{"callee":"productcatalogservice","caller":"checkoutservice"},{"callee":"checkoutservice","caller":"frontend"},{"callee":"productcatalogservice","caller":"frontend"},{"callee":"recommendationservice","caller":"frontend"},{"callee":"productcatalogservice","caller":"recommendationservice"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

{"confidence":"high","reason":"Rank checkoutservice first because checkoutservice has direct container-cpu-system-seconds-total evidence (signed-z 465.95, persistence 11 bins); although frontend is salient, the caller path frontend -> checkoutservice means a disturbance in the callee can propagate back toward that caller-side symptom.","services":["checkoutservice","frontend"]}

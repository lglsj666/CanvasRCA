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
opaque_id: INC-9898D93921DC
observation_window={"duration_rel_s":1440.0,"source_metric_rows":1441}
selection_summary={"candidate_count":17,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":264,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["adservice","cartservice","checkoutservice","currencyservice","emailservice","frontend","frontend-external","gke-gke-cluster-default-pool-2e1807ce-0e4z","gke-gke-cluster-default-pool-2e1807ce-cx8g","gke-gke-cluster-default-pool-2e1807ce-w819","gke-gke-cluster-default-pool-2e1807ce-xte3","loadgenerator","paymentservice","productcatalogservice","recommendationservice","redis","shippingservice"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[11.25,33.75,56.25,78.75,101.25,123.75,146.25,168.75,191.25,213.75,236.25,258.75,281.25,303.75,326.25,348.75,371.25,393.75,416.25,438.75,461.25,483.75,506.25,528.75,551.25,573.75,596.25,618.75,641.25,663.75,686.25,708.75,731.25,753.75,776.25,798.75,821.25,843.75,866.25,888.75,911.25,933.75,956.25,978.75,1001.25,1023.75,1046.25,1068.75,1091.25,1113.75,1136.25,1158.75,1181.25,1203.75,1226.25,1248.75,1271.25,1293.75,1316.25,1338.75,1361.25,1383.75,1406.25,1428.75]
[M1] rank=1 service=checkoutservice metric=container-memory-mapped-file baseline=0.0 peak=2215936.0 signed_z=999.0 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=rle:0*33,2215936*31
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M2] rank=2 service=gke-gke-cluster-default-pool-2e1807ce-w819 metric=node-memory-active-bytes baseline=2727.000494 peak=22209058.133333 signed_z=999.0 onset_bin=46 onset_rel_s=1046.25 persistence_bins=2
values_compact=delta:2639.644444,-182.044444,91.022222,546.133334,-91.022223,0,-364.088889,-910.222222,364.088889,1183.288889,-91.022222,-728.177778,91.022222,364.088889,273.066667,-364.088889,-273.066667,91.022222,273.066667,364.088889,0,-91.022222,-728.177778,-455.111111,637.155555,-364.088888,-273.066667,273.066667,364.088888,364.088889,-273.066666,1092.266666,273.066667,-1274.311111,-455.111111,182.044444,637.155556,182.044444,-364.088889,91.022223,0,-91.022223,0,182.044445,728.177778,-546.133334,22205599.288889,-91.022222,-22206509.511111,182.044444,273.066667,-91.022222,-182.044445,91.022222,546.133334,-182.044445,-364.088889,-546.133333,1729.422222,-273.066666,-1729.422223,1001.244445,-91.022222,364.088889
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M3] rank=3 service=checkoutservice metric=container-sockets baseline=9.0 peak=23.0 signed_z=608.696 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=rle:9*33,22*3,23*1,22*27
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M4] rank=4 service=checkoutservice metric=container-cpu-system-seconds-total baseline=0.143506 peak=14.830163 signed_z=537.687 onset_bin=33 onset_rel_s=753.75 persistence_bins=6
values_compact=raw:[0.106243,0.113546,0.118589,0.143556,0.175094,0.133909,0.116137,0.15025,0.173353,0.168306,0.103046,0.158521,0.181588,0.176896,0.119463,0.11996,0.148352,0.152801,0.1221,0.090129,0.134804,0.154416,0.141441,0.138038,0.125544,0.159955,0.161022,0.170851,0.173926,0.159605,0.160987,0.187107,0.208771,9.151948,14.436374,14.567211,14.462739,10.592685,5.133958,0.142717,0.087627,0.107308,0.168968,0.143287,0.101301,0.124606,0.159468,0.160906,0.129601,0.12465,0.179176,0.119145,0.106885,0.135426,0.15353,0.111339,0.172089,0.156744,0.128376,0.160289,0.199487,0.167228,0.120305,0.116282]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M5] rank=5 service=checkoutservice metric=container-cpu-usage-seconds-total baseline=0.413281 peak=19.214292 signed_z=233.469 onset_bin=33 onset_rel_s=753.75 persistence_bins=6
values_compact=raw:[0.309837,0.339843,0.338805,0.406302,0.474648,0.345365,0.271531,0.396152,0.471164,0.52689,0.326145,0.461958,0.507394,0.501146,0.387878,0.341734,0.3981,0.464232,0.354057,0.257597,0.387053,0.430617,0.430956,0.448597,0.410654,0.457107,0.479941,0.486094,0.465722,0.431477,0.434414,0.526704,0.551307,11.806801,18.525109,18.821221,18.801183,13.801332,6.811624,0.357494,0.256676,0.334247,0.501036,0.408104,0.310816,0.360234,0.438774,0.440534,0.336221,0.348162,0.499043,0.371201,0.31835,0.398041,0.395633,0.271916,0.425081,0.36866,0.331603,0.40787,0.510937,0.502834,0.404978,0.37242]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M6] rank=6 service=checkoutservice metric=container-memory-cache baseline=0.0 peak=2215936.0 signed_z=160.667 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=rle:0*33,2215936*31
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M7] rank=7 service=checkoutservice metric=container-cpu-user-seconds-total baseline=0.269776 peak=4.384129 signed_z=73.178 onset_bin=33 onset_rel_s=753.75 persistence_bins=6
values_compact=raw:[0.203597,0.224858,0.220214,0.262744,0.299554,0.211458,0.155396,0.245902,0.297811,0.358582,0.2231,0.30998,0.325808,0.325542,0.270707,0.230997,0.249748,0.311429,0.231955,0.163491,0.252249,0.276201,0.289515,0.315729,0.285107,0.297152,0.318919,0.320156,0.288253,0.271875,0.273426,0.339597,0.342538,2.65485,4.088733,4.254012,4.358042,3.208645,1.677666,0.214776,0.169051,0.226939,0.32915,0.26482,0.209518,0.235628,0.279306,0.279626,0.20662,0.223512,0.319867,0.252056,0.211465,0.262616,0.242103,0.160576,0.249122,0.211916,0.20586,0.247584,0.311448,0.333142,0.284675,0.256139]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M8] rank=8 service=checkoutservice metric=container-memory-failures-total baseline=2.997042 peak=120.826154 signed_z=66.522 onset_bin=33 onset_rel_s=753.75 persistence_bins=2
values_compact=raw:[4.237864,8.451764,7.157821,4.009339,4.245059,2.287619,2.593881,1.930654,0.300282,4.312074,0.445253,0.856266,1.217162,3.330599,4.12276,2.450213,1.733774,1.402932,2.660381,2.982444,3.607044,2.737091,2.768425,3.871555,3.546761,0.539993,1.339614,3.102022,3.251398,4.184389,4.602992,1.815967,0.49552,93.566446,88.900341,1.67364,0.301152,2.483875,5.270675,4.134486,0.757432,3.147932,3.29053,0.800944,1.282902,2.915713,2.236488,1.266123,1.394671,0.572316,0.954466,0.606205,0.083788,0.552294,4.917151,6.683641,3.83437,1.040638,0.367397,3.227661,4.254666,3.172114,2.951245,2.863051]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M9] rank=9 service=checkoutservice metric=container-memory-usage-bytes baseline=11442471.822222 peak=22564864.0 signed_z=53.153 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=delta:11739136,-491520,73728,245760,-131072,-24576,176128,-311296,0,331776,12288,-311296,53248,-348160,163840,69632,-225280,94208,139264,106496,229376,36864,-159744,114688,36864,4096,118784,-159744,69632,307200,-409600,20480,8192,10985472,-2273280,-421888,2048000,258048,-172032,43008,34816,270336,16384,-557056,49152,212992,12288,86016,-2207744,12288,-8192,-2248704,-2240512,-200704,86016,217088,-450560,4096,16384,-159744,110592,57344,245760,16384
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M10] rank=10 service=checkoutservice metric=container-memory-working-set-bytes baseline=11442471.822222 peak=22564864.0 signed_z=53.153 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=delta:11739136,-491520,73728,245760,-131072,-24576,176128,-311296,0,331776,12288,-311296,53248,-348160,163840,69632,-225280,94208,139264,106496,229376,36864,-159744,114688,36864,4096,118784,-159744,69632,307200,-409600,20480,8192,10985472,-2273280,-421888,2048000,258048,-172032,43008,34816,270336,16384,-557056,49152,212992,12288,86016,-2207744,12288,-8192,-2248704,-2240512,-200704,86016,217088,-450560,4096,16384,-159744,110592,57344,245760,16384
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M11] rank=11 service=emailservice metric=container-network-receive-bytes-total baseline=807.277463 peak=7134.200732 signed_z=48.075 onset_bin=40 onset_rel_s=911.25 persistence_bins=2
values_compact=delta:736.186846,42.015101,-16.636836,63.834495,-1.204552,-53.326936,-66.236409,51.683958,179.833223,63.518124,-87.795533,17.483463,-28.51391,-109.306385,80.315512,-441.348933,326.106621,113.751282,-3.007595,-190.302865,-117.172977,316.888419,-150.261011,179.693504,-95.471433,137.392856,-95.104938,-17.066167,69.950528,2.836533,-3.92533,9.340126,-32.169637,102.711277,-140.824922,0,88.438104,-97.334685,-49.529066,-270.688264,4173.681611,-4324.488114,659.968634,-195.006071,-145.144339,105.162799,97.117609,-57.205913,-67.564446,-4.706032,46.436488,36.645972,-43.200438,116.463871,-99.105621,0.772472,-124.165562,0,77.625936,45.527932,108.906894,84.856663,-177.781537,-62.638557
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M12] rank=12 service=paymentservice metric=istio-latency-95 baseline=0.008471 peak=0.0975 signed_z=30.486 onset_bin=42 onset_rel_s=956.25 persistence_bins=5
values_compact=raw:[0.009,0.008062,0.005125,0.007437,0.008125,0.0085,0.00865,0.009083,0.008542,0.008425,0.009021,0.008438,0.00735,0.008179,0.008563,0.00815,0.006833,0.00825,0.00875,0.008438,0.006667,0.007312,0.007958,0.007,0.004879,0.004875,0.0079,0.00875,0.0098,0.02125,0.009675,0.009852,0.009792,0.009566,0.013,0.01,0.009375,0.009527,0.009487,0.009404,0.009125,0.009705,0.02125,0.059167,0.05625,0.013,0.009431,0.009154,0.009,0.009167,0.008833,0.008063,0.00875,0.008687,0.00525,0.005875,0.0081,0.008719,0.008944,0.0089,0.008639,0.06125,0.0975,0.009321]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[710.0,1440.0]

=== LOG SUMMARY ===
{"entries":[{"change_pct":-33.3,"n_during":10,"n_pre":15,"service":"redis"},{"change_pct":-5.1,"n_during":333,"n_pre":351,"service":"emailservice"},{"change_pct":-4.9,"n_during":1001,"n_pre":1053,"service":"checkoutservice"},{"change_pct":-4.8,"n_during":668,"n_pre":702,"service":"paymentservice"},{"change_pct":-1.9,"n_during":27703,"n_pre":28248,"service":"currencyservice"},{"change_pct":-1.6,"n_during":5266,"n_pre":5352,"service":"shippingservice"},{"change_pct":1.0,"n_during":5431,"n_pre":5379,"service":"adservice"},{"change_pct":1.0,"n_during":6769,"n_pre":6705,"service":"recommendationservice"}],"mode":"volume","omitted_services":2,"service_count":10}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":26.6,"error_pct":0.0,"p95_during_ms":99.25019999999999,"p95_pre_ms":78.4228,"service":"checkoutservice","spans":9429},{"delta_pct":24.6,"error_pct":0.0,"p95_during_ms":0.5529999999999992,"p95_pre_ms":0.44379999999999964,"service":"paymentservice","spans":973},{"delta_pct":11.1,"error_pct":0.0,"p95_during_ms":0.4569999999999998,"p95_pre_ms":0.41129999999999994,"service":"emailservice","spans":1260},{"delta_pct":-2.0,"error_pct":0.0,"p95_during_ms":0.248,"p95_pre_ms":0.253,"service":"currencyservice","spans":56236},{"delta_pct":-1.6,"error_pct":0.0,"p95_during_ms":67.26245,"p95_pre_ms":68.355,"service":"frontend","spans":206083},{"delta_pct":1.3,"error_pct":0.0,"p95_during_ms":4.594099999999998,"p95_pre_ms":4.537,"service":"recommendationservice","spans":27524},{"delta_pct":0.0,"error_pct":0.0,"p95_during_ms":0.025,"p95_pre_ms":0.025,"service":"productcatalogservice","spans":103094}],"omitted_services":0,"service_count":7}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=3 omitted_edges=0
[{"evidence_source":"trace","onset_rel_s":735.0,"rank":1,"service":"checkoutservice","severity_z":22.253},{"evidence_source":"trace","onset_rel_s":765.0,"rank":2,"service":"paymentservice","severity_z":19.081},{"evidence_source":"metric","onset_rel_s":1033.8,"rank":3,"service":"gke-gke-cluster-default-pool-2e1807ce-w819","severity_z":999.0},{"evidence_source":"trace","onset_rel_s":1065.0,"rank":4,"service":"emailservice","severity_z":7.077},{"evidence_source":"metric","onset_rel_s":1231.2,"rank":5,"service":"adservice","severity_z":12.173},{"evidence_source":"metric","onset_rel_s":1263.0,"rank":6,"service":"shippingservice","severity_z":24.385},{"evidence_source":"metric","onset_rel_s":1306.8,"rank":7,"service":"redis","severity_z":22.718},{"evidence_source":"metric","onset_rel_s":1378.2,"rank":8,"service":"frontend","severity_z":22.674},{"evidence_source":"none","onset_rel_s":null,"rank":9,"service":"gke-gke-cluster-default-pool-2e1807ce-0e4z","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":10,"service":"recommendationservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":11,"service":"gke-gke-cluster-default-pool-2e1807ce-cx8g","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":12,"service":"gke-gke-cluster-default-pool-2e1807ce-xte3","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":13,"service":"cartservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":14,"service":"productcatalogservice","severity_z":0.0}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"emailservice","caller":"checkoutservice"},{"callee":"paymentservice","caller":"checkoutservice"},{"callee":"productcatalogservice","caller":"checkoutservice"},{"callee":"checkoutservice","caller":"frontend"},{"callee":"productcatalogservice","caller":"frontend"},{"callee":"recommendationservice","caller":"frontend"},{"callee":"productcatalogservice","caller":"recommendationservice"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

{"confidence":"high","reason":"Rank checkoutservice first because checkoutservice has direct container-memory-mapped-file evidence (signed-z 999, persistence 31 bins); although frontend is salient, the caller path frontend -> checkoutservice means a disturbance in the callee can propagate back toward that caller-side symptom.","services":["checkoutservice","frontend"]}

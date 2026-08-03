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
opaque_id: INC-CC386164065D
observation_window={"duration_rel_s":1440.0,"source_metric_rows":1441}
selection_summary={"candidate_count":17,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":266,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["adservice","cartservice","checkoutservice","currencyservice","emailservice","frontend","frontend-external","gke-gke-cluster-default-pool-2e1807ce-0e4z","gke-gke-cluster-default-pool-2e1807ce-cx8g","gke-gke-cluster-default-pool-2e1807ce-w819","gke-gke-cluster-default-pool-2e1807ce-xte3","loadgenerator","paymentservice","productcatalogservice","recommendationservice","redis","shippingservice"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[11.25,33.75,56.25,78.75,101.25,123.75,146.25,168.75,191.25,213.75,236.25,258.75,281.25,303.75,326.25,348.75,371.25,393.75,416.25,438.75,461.25,483.75,506.25,528.75,551.25,573.75,596.25,618.75,641.25,663.75,686.25,708.75,731.25,753.75,776.25,798.75,821.25,843.75,866.25,888.75,911.25,933.75,956.25,978.75,1001.25,1023.75,1046.25,1068.75,1091.25,1113.75,1136.25,1158.75,1181.25,1203.75,1226.25,1248.75,1271.25,1293.75,1316.25,1338.75,1361.25,1383.75,1406.25,1428.75]
[M1] rank=1 service=emailservice metric=container-memory-failures-total baseline=0.059183 peak=163.852209 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=rle:0.079903*1,0.087627*1,0.058662*1,0.044147*1,0*1,0.193603*1,0.188083*1,0*5,0.041635*1,0.046113*1,0.03501*1,0.052461*1,0.052182*1,0.345423*1,0.063696*1,0.040678*1,0*3,0.045282*1,0.038324*1,0*3,0.199432*1,0.158964*1,0*2,0.059173*1,126.775097*1,0*6,0.16093*1,0.147569*1,0.038365*1,0*7,0.090263*1,0.134538*1,0.122266*1,0.04957*1,0*2,0.042552*1,0.045187*1,0*3,0.05284*1,0.146863*1,0.068025*1
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M2] rank=2 service=emailservice metric=container-memory-mapped-file baseline=0.0 peak=2289664.0 signed_z=999.0 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=rle:0*33,2289664*31
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M3] rank=3 service=emailservice metric=istio-latency-90 baseline=0.00461 peak=0.06125 signed_z=999.0 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=rle:0.0046*1,0.004687*1,0.004669*1,0.0046*19,0.004669*1,0.004673*1,0.0046*9,0.018004*1,0.021368*1,0.021948*1,0.022437*1,0.023279*1,0.05875*1,0.039576*1,0.022913*1,0.02238*1,0.022964*1,0.0235*1,0.023125*1,0.022916*1,0.022932*1,0.022718*1,0.022346*1,0.022032*1,0.0223*1,0.023508*1,0.023552*1,0.02284*1,0.022088*1,0.022625*1,0.022414*1,0.02005*1,0.0226*1,0.022675*1,0.022*1,0.022478*1,0.022556*1,0.021523*1
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M4] rank=4 service=emailservice metric=istio-latency-95 baseline=0.004811 peak=0.080625 signed_z=999.0 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=rle:0.0048*1,0.004892*1,0.004873*1,0.0048*19,0.004873*1,0.004877*1,0.0048*9,0.021502*1,0.023184*1,0.023474*1,0.023719*1,0.042507*1,0.079375*1,0.068125*1,0.023957*1,0.023829*1,0.024518*1,0.024547*1,0.024063*1,0.023958*1,0.023966*1,0.023859*1,0.023673*1,0.023516*1,0.02365*1,0.024713*1,0.024793*1,0.02407*1,0.023544*1,0.023813*1,0.023707*1,0.022525*1,0.0238*1,0.023837*1,0.0235*1,0.023739*1,0.023778*1,0.023261*1
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M5] rank=5 service=gke-gke-cluster-default-pool-2e1807ce-0e4z metric=node-memory-active-bytes baseline=9882.358519 peak=17150498.133333 signed_z=999.0 onset_bin=42 onset_rel_s=956.25 persistence_bins=2
values_compact=delta:12288,-1911.466667,-2457.6,1729.422223,1456.355555,-1092.266667,-819.2,455.111112,546.133333,1092.266667,-637.155556,1092.266667,4551.111111,-2639.644445,-6826.666666,1638.4,2639.644444,-546.133333,91.022222,1183.288889,-2548.622222,-2730.666667,364.088889,910.222222,91.022222,1365.333334,455.111111,-1092.266667,-182.044444,-1729.422223,3640.888889,1638.4,-3367.822222,-1638.4,910.222222,-546.133333,-3185.777778,546.133334,4004.977777,1092.266667,-1547.377778,-455.111111,17142670.222222,-273.066666,-17143489.422223,2821.688889,1001.244445,-3640.888889,-1729.422222,-728.177778,1183.288889,2275.555555,2275.555556,819.2,-1729.422222,-455.111111,-273.066667,-1456.355556,3458.844445,2548.622222,-3731.911111,-2184.533333,273.066666,91.022222
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M6] rank=6 service=emailservice metric=istio-latency-50 baseline=0.003006 peak=0.016848 signed_z=881.006 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=rle:0.003*1,0.003048*1,0.003038*1,0.003*19,0.003038*1,0.003041*1,0.003*9,0.004006*1,0.008*1,0.009906*1,0.012188*1,0.012868*1,0.014737*1,0.015897*1,0.014565*1,0.010295*1,0.010536*1,0.01545*1,0.015625*1,0.014582*1,0.014662*1,0.01359*1,0.011731*1,0.009978*1,0.0115*1,0.01358*1,0.013621*1,0.013*1,0.010441*1,0.013125*1,0.012069*1,0.006898*1,0.013*1,0.013373*1,0.01*1,0.012389*1,0.012778*1,0.008542*1
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M7] rank=7 service=emailservice metric=container-cpu-user-seconds-total baseline=0.209495 peak=20.037272 signed_z=764.392 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=delta:0.213599,0.039365,-0.010793,-0.010268,-0.023002,0.002289,-0.009129,-0.013,0.020241,-0.003857,-0.002659,0.014803,0.000037,0.005334,-0.014235,0.014037,-0.034554,0.036197,-0.034344,0.040874,-0.028436,0.010386,-0.005485,0.034466,-0.00531,-0.021751,-0.013448,0.003756,-0.027615,0.033924,0.022788,-0.002185,-0.00761,6.463758,13.290488,0.010219,0.017947,0.014468,-0.031522,0.003267,0.023506,-0.03166,0.019039,-4.044239,4.044857,-3.643835,3.631505,0.026847,-0.031703,0.001254,0.001808,0.009908,-0.008044,0.010733,-0.012386,0.011651,0.002167,-0.027403,0.002214,0.034743,-0.036377,0,0.014391,0.005501
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M8] rank=8 service=emailservice metric=container-cpu-usage-seconds-total baseline=0.277987 peak=20.037272 signed_z=640.081 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=delta:0.250423,0.056565,-0.000024,-0.004423,-0.013706,0.001979,-0.009274,-0.016473,0.013739,-0.010917,-0.0053,0.020014,0.001834,0.00747,-0.015586,0.007909,-0.046477,0.073972,-0.071076,0.068583,-0.02006,0.004993,-0.022329,0.037713,0.005003,-0.021471,-0.014507,0.013104,-0.040354,0.04046,0.002814,-0.001106,0.001765,6.441935,13.241467,0.01022,0.017948,0.014468,-0.031522,0.003269,0.023504,-0.031662,0.019041,-4.044239,4.044857,-3.643835,3.631505,0.026847,-0.031703,0.001254,0.001808,0.009908,-0.008042,0.010728,-0.012383,0.011651,0.002167,-0.027403,0.002214,0.034743,-0.036375,0,0.014389,0.005501
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M9] rank=9 service=emailservice metric=container-memory-rss baseline=40864870.4 peak=44089344.0 signed_z=416.875 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=delta:40853504,0,4096,0,0,-2048,2048,0,0,0,0,0,4096,0,0,4096,0,0,4096,0,0,0,0,4096,0,0,0,0,0,0,0,0,4096,3190784,0,0,0,0,0,0,8192,4096,0,0,0,0,0,0,0,0,-8192,4096,0,4096,0,0,4096,0,0,0,0,4096,-4096,0
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M10] rank=10 service=cartservice metric=istio-latency-90 baseline=0.005167 peak=0.243437 signed_z=400.918 onset_bin=47 onset_rel_s=1068.75 persistence_bins=3
values_compact=raw:[0.004887,0.00495,0.004881,0.004878,0.004955,0.007127,0.005718,0.004815,0.004784,0.004827,0.004812,0.004782,0.004894,0.004922,0.005302,0.005982,0.00497,0.00497,0.006568,0.004975,0.004761,0.004855,0.005937,0.004921,0.004772,0.004847,0.005377,0.006636,0.004904,0.004825,0.004949,0.004915,0.004798,0.004817,0.004746,0.004722,0.004794,0.004803,0.004853,0.004858,0.004853,0.004845,0.004965,0.004938,0.004819,0.004888,0.004994,0.237812,0.151429,0.004921,0.004733,0.004997,0.005881,0.00477,0.004909,0.00953,0.004932,0.004833,0.004812,0.004734,0.004721,0.004696,0.004732,0.004778]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M11] rank=11 service=emailservice metric=container-sockets baseline=3.0 peak=5.0 signed_z=400.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=rle:3*36,5*1,3*11,5*1,3*15
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M12] rank=12 service=emailservice metric=container-memory-usage-bytes baseline=43748573.866667 peak=49856512.0 signed_z=283.82 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=delta:43732992,0,4096,0,4096,-6144,2048,4096,-4096,4096,-4096,4096,0,0,0,4096,0,4096,0,4096,0,-4096,4096,4096,126976,-126976,-4096,2048,2048,0,-4096,0,4096,6074368,4096,0,8192,-12288,4096,0,8192,4096,-4096,0,4096,8192,-12288,0,12288,-12288,-4096,0,8192,0,0,0,4096,-4096,4096,-4096,0,4096,0,0
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[708.0,1440.0]

=== LOG SUMMARY ===
{"entries":[{"change_pct":50.0,"n_during":15,"n_pre":10,"service":"redis"},{"change_pct":15.4,"n_during":344,"n_pre":298,"service":"emailservice"},{"change_pct":15.4,"n_during":688,"n_pre":596,"service":"paymentservice"},{"change_pct":15.2,"n_during":1031,"n_pre":895,"service":"checkoutservice"},{"change_pct":3.3,"n_during":5310,"n_pre":5142,"service":"shippingservice"},{"change_pct":3.1,"n_during":5219,"n_pre":5062,"service":"adservice"},{"change_pct":2.9,"n_during":6580,"n_pre":6394,"service":"recommendationservice"},{"change_pct":2.0,"n_during":8957,"n_pre":8784,"service":"cartservice"}],"mode":"volume","omitted_services":2,"service_count":10}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":2677.2,"error_pct":0.0,"p95_during_ms":9.68975,"p95_pre_ms":0.3488999999999998,"service":"emailservice","spans":1218},{"delta_pct":-25.7,"error_pct":0.0,"p95_during_ms":0.6079499999999978,"p95_pre_ms":0.8180499999999999,"service":"paymentservice","spans":930},{"delta_pct":4.0,"error_pct":0.0,"p95_during_ms":221.69650000000001,"p95_pre_ms":213.0992,"service":"checkoutservice","spans":8920},{"delta_pct":-2.6,"error_pct":0.0,"p95_during_ms":191.00719999999998,"p95_pre_ms":196.1975999999996,"service":"frontend","spans":199952},{"delta_pct":1.3,"error_pct":0.0,"p95_during_ms":0.183,"p95_pre_ms":0.1806499999999978,"service":"currencyservice","spans":55072},{"delta_pct":1.1,"error_pct":0.0,"p95_during_ms":4.988,"p95_pre_ms":4.935449999999999,"service":"recommendationservice","spans":26524},{"delta_pct":0.0,"error_pct":0.0,"p95_during_ms":0.023,"p95_pre_ms":0.023,"service":"productcatalogservice","spans":99804}],"omitted_services":0,"service_count":7}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=3 omitted_edges=0
[{"evidence_source":"trace","onset_rel_s":735.0,"rank":1,"service":"emailservice","severity_z":201.04},{"evidence_source":"metric","onset_rel_s":892.2,"rank":2,"service":"adservice","severity_z":53.516},{"evidence_source":"metric","onset_rel_s":955.8,"rank":3,"service":"gke-gke-cluster-default-pool-2e1807ce-0e4z","severity_z":999.0},{"evidence_source":"trace","onset_rel_s":1035.0,"rank":4,"service":"recommendationservice","severity_z":6.267},{"evidence_source":"metric","onset_rel_s":1060.2,"rank":5,"service":"cartservice","severity_z":400.918},{"evidence_source":"metric","onset_rel_s":1209.0,"rank":6,"service":"productcatalogservice","severity_z":55.996},{"evidence_source":"none","onset_rel_s":null,"rank":7,"service":"currencyservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":8,"service":"gke-gke-cluster-default-pool-2e1807ce-xte3","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":9,"service":"shippingservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":10,"service":"frontend","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":11,"service":"loadgenerator","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":12,"service":"redis","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":13,"service":"paymentservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":14,"service":"checkoutservice","severity_z":0.0}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"currencyservice","caller":"checkoutservice"},{"callee":"emailservice","caller":"checkoutservice"},{"callee":"paymentservice","caller":"checkoutservice"},{"callee":"productcatalogservice","caller":"checkoutservice"},{"callee":"checkoutservice","caller":"frontend"},{"callee":"currencyservice","caller":"frontend"},{"callee":"productcatalogservice","caller":"frontend"},{"callee":"recommendationservice","caller":"frontend"},{"callee":"productcatalogservice","caller":"recommendationservice"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

{"confidence":"high","reason":"Rank emailservice first because emailservice has direct container-memory-failures-total evidence (signed-z 999, persistence 0 bins); although checkoutservice is salient, the caller path checkoutservice -> emailservice means a disturbance in the callee can propagate back toward that caller-side symptom.","services":["emailservice","checkoutservice"]}

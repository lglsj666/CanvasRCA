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
opaque_id: INC-C53E61CF4333
observation_window={"duration_rel_s":1440.0,"source_metric_rows":1441}
selection_summary={"candidate_count":17,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":264,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["adservice","cartservice","checkoutservice","currencyservice","emailservice","frontend","frontend-external","gke-gke-cluster-default-pool-2e1807ce-0e4z","gke-gke-cluster-default-pool-2e1807ce-cx8g","gke-gke-cluster-default-pool-2e1807ce-w819","gke-gke-cluster-default-pool-2e1807ce-xte3","loadgenerator","paymentservice","productcatalogservice","recommendationservice","redis","shippingservice"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[11.25,33.75,56.25,78.75,101.25,123.75,146.25,168.75,191.25,213.75,236.25,258.75,281.25,303.75,326.25,348.75,371.25,393.75,416.25,438.75,461.25,483.75,506.25,528.75,551.25,573.75,596.25,618.75,641.25,663.75,686.25,708.75,731.25,753.75,776.25,798.75,821.25,843.75,866.25,888.75,911.25,933.75,956.25,978.75,1001.25,1023.75,1046.25,1068.75,1091.25,1113.75,1136.25,1158.75,1181.25,1203.75,1226.25,1248.75,1271.25,1293.75,1316.25,1338.75,1361.25,1383.75,1406.25,1428.75]
[M1] rank=1 service=checkoutservice metric=container-memory-failures-total baseline=3.500149 peak=42734.596338 signed_z=999.0 onset_bin=32 onset_rel_s=731.25 persistence_bins=32
values_compact=delta:2.473207,1.998338,1.234102,0.035757,0.429195,-1.430221,-1.07395,-2.697436,0.815744,-0.08196,-1.474048,0.684799,2.284524,1.326057,2.255391,-1.037146,0.347677,0.144902,-3.302381,-0.349895,-0.200916,0.401264,2.193941,0.802474,-1.805725,-2.644247,1.292718,0.85125,-0.326627,-1.197254,0.131054,0.763143,6685.95934,13715.270228,13385.327432,6701.198422,-605.664997,1444.296526,609.900538,-1345.116674,-62.01823,1130.413814,471.925107,-3112.147323,1276.578093,1093.738112,-2250.169424,1657.314103,860.276232,-1053.551638,-1268.598038,107.699236,521.313424,-513.816519,743.922834,278.536961,-133.24208,1532.288911,-2039.259354,884.737259,-316.208341,-256.846339,887.20557,-907.006499
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M2] rank=2 service=checkoutservice metric=container-memory-mapped-file baseline=0.0 peak=2211840.0 signed_z=999.0 onset_bin=32 onset_rel_s=731.25 persistence_bins=32
values_compact=rle:0*32,2211840*32
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M3] rank=3 service=checkoutservice metric=container-memory-rss baseline=10851652.266667 peak=264953856.0 signed_z=999.0 onset_bin=32 onset_rel_s=731.25 persistence_bins=32
values_compact=delta:10682368,196608,229376,-159744,131072,-241664,8192,28672,147456,-331776,12288,65536,-262144,311296,290816,-180224,-28672,225280,-446464,208896,8192,262144,-622592,348160,-331776,45056,237568,131072,73728,-434176,143360,131072,254074880,-121643008,121638912,-143863808,143867904,-65527808,65527808,-20480,0,-78143488,78159872,4096,0,0,0,0,-31551488,31531008,-185139200,185139200,-4096,-208011264,208015360,-20480,20480,0,0,-55529472,-81657856,74956800,-101261312,163491840
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M4] rank=4 service=checkoutservice metric=container-memory-usage-bytes baseline=11369432.177778 peak=268439552.0 signed_z=999.0 onset_bin=32 onset_rel_s=731.25 persistence_bins=32
values_compact=delta:11198464,192512,229376,-155648,126976,-241664,8192,28672,176128,-360448,16384,61440,-262144,311296,290816,-176128,-32768,225280,-430080,192512,12288,262144,-622592,344064,-331776,73728,212992,126976,77824,-417792,122880,159744,257011712,-121876480,121880576,-144130048,144130048,-65634304,65634304,-8192,-8192,-78303232,78319616,4096,-4096,0,0,0,-31608832,31596544,-185397248,185409536,0,-208076800,208076800,-12288,12288,0,0,-55574528,-63569920,56791040,-101437440,163790848
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M5] rank=5 service=checkoutservice metric=container-memory-working-set-bytes baseline=11369432.177778 peak=268439552.0 signed_z=999.0 onset_bin=32 onset_rel_s=731.25 persistence_bins=32
values_compact=delta:11198464,192512,229376,-155648,126976,-241664,8192,28672,176128,-360448,16384,61440,-262144,311296,290816,-176128,-32768,225280,-430080,192512,12288,262144,-622592,344064,-331776,73728,212992,126976,77824,-417792,122880,159744,257011712,-121876480,121880576,-144130048,144130048,-65634304,65634304,-8192,-8192,-78303232,78319616,4096,-4096,0,0,0,-31608832,31596544,-185397248,185409536,0,-208076800,208076800,-12288,12288,0,0,-55574528,-63569920,56791040,-101437440,163790848
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M6] rank=6 service=gke-gke-cluster-default-pool-2e1807ce-w819 metric=node-memory-active-bytes baseline=2387.816296 peak=17594413.511111 signed_z=999.0 onset_bin=57 onset_rel_s=1293.75 persistence_bins=2
values_compact=delta:2275.555556,0,182.044444,546.133333,182.044445,91.022222,-364.088889,-819.2,-91.022222,0,182.044444,-273.066666,273.066666,364.088889,-273.066666,364.088888,728.177778,-728.177778,-728.177777,455.111111,-364.088889,91.022222,273.066667,-546.133334,0,364.088889,0,0,182.044445,273.066666,91.022223,-182.044445,-364.088889,91.022223,91.022222,91.022222,-91.022222,0,273.066666,91.022223,-182.044445,0,182.044445,-182.044445,0,91.022222,-546.133333,-273.066667,182.044445,-273.066667,364.088889,637.155556,364.088889,-364.088889,-728.177778,-546.133333,455.111111,17592502.044444,-455.111111,-17592046.933333,455.111111,-182.044445,-819.2,273.066667
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M7] rank=7 service=gke-gke-cluster-default-pool-2e1807ce-xte3 metric=node-memory-active-bytes baseline=6426.800988 peak=21632068.266667 signed_z=999.0 onset_bin=49 onset_rel_s=1113.75 persistence_bins=2
values_compact=delta:8100.977778,-273.066667,-728.177778,364.088889,-364.088889,-1820.444444,-182.044445,2002.488889,-819.2,-819.2,273.066667,1092.266667,-91.022223,-455.111111,455.111111,0,273.066667,-1092.266667,-364.088888,-182.044445,364.088889,910.222222,-1183.288889,455.111111,2184.533334,637.155555,-1638.4,-2366.577777,637.155555,1092.266667,-910.222222,728.177777,1911.466667,-273.066667,-1274.311111,1092.266667,819.2,-2093.511111,-2184.533334,273.066667,1729.422222,2184.533334,-455.111111,-910.222223,-273.066666,-3003.733334,0,2548.622223,-273.066667,21625696.711111,273.066667,-21624604.444445,-1547.377778,-1365.333333,1092.266667,546.133333,1638.4,-1274.311111,1365.333333,-819.2,-3003.733333,2002.488889,546.133333,-1092.266666
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M8] rank=8 service=gke-gke-cluster-default-pool-2e1807ce-0e4z metric=node-disk-reads-completed-total baseline=0.0 peak=0.8 signed_z=999.0 onset_bin=33 onset_rel_s=753.75 persistence_bins=4
values_compact=rle:0*33,0.111111*2,0*1,0.8*2,0*26
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M9] rank=9 service=gke-gke-cluster-default-pool-2e1807ce-0e4z metric=node-disk-read-bytes-total baseline=0.0 peak=9557.333333 signed_z=999.0 onset_bin=33 onset_rel_s=753.75 persistence_bins=4
values_compact=rle:0*33,455.111111*2,0*1,9557.333333*2,0*26
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M10] rank=10 service=checkoutservice metric=container-cpu-system-seconds-total baseline=0.142702 peak=15.702736 signed_z=497.288 onset_bin=32 onset_rel_s=731.25 persistence_bins=32
values_compact=delta:0.138095,0.052299,-0.01023,-0.033417,0.019295,-0.028058,-0.005431,-0.02332,0.010884,-0.013561,0.026845,0.012225,-0.015024,0.024644,0.041134,-0.031246,-0.009949,0.007622,-0.011693,-0.035491,-0.003516,-0.007254,0.035482,0.015959,-0.001397,-0.018905,-0.043766,0.056713,0.010969,0.00841,0.019732,-0.016026,2.328272,3.358229,4.088817,1.884792,0.346368,0.560542,0.458513,-0.027988,0.070159,0.681912,0.413252,-0.151881,0.062048,0.562256,-0.19971,0.0363,0.072012,-0.033835,-0.053568,0.318026,0.108276,-0.57744,0.46048,0.330213,0.172819,0.18375,-0.699663,-0.178992,0.334075,0.072656,0.237283,-0.246483
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M11] rank=11 service=checkoutservice metric=container-sockets baseline=9.0 peak=14.0 signed_z=357.143 onset_bin=32 onset_rel_s=731.25 persistence_bins=32
values_compact=rle:9*32,12*7,14*1,12*24
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M12] rank=12 service=shippingservice metric=istio-latency-99 baseline=0.004966 peak=0.00776 signed_z=289.156 onset_bin=50 onset_rel_s=1136.25 persistence_bins=3
values_compact=delta:0.004968,0,0.000001,0,-0.000001,-0.000011,0,0.000013,-0.000001,-0.000012,0.000001,0.000013,0,-0.000003,0,-0.000011,-0.000001,0,0,-0.000001,0.000001,0.000023,0.000001,-0.000024,0,0.000013,0.000002,0.000023,-0.000003,-0.000034,0,0.000021,0.000013,-0.000023,-0.000011,0.000009,0.000001,-0.000012,0.000001,0.000038,0.000306,-0.000342,0,0.000011,-0.000001,-0.000012,0.000013,0.000014,-0.000014,0.000017,0.001897,0.000217,-0.0021,-0.000022,-0.00001,-0.000012,0.000001,0.000012,0.000001,-0.000013,0.000013,0.000001,-0.000013,-0.000001
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[707.0,1440.0]

=== LOG SUMMARY ===
{"entries":[{"change_pct":50.0,"n_during":15,"n_pre":10,"service":"redis"},{"change_pct":7.9,"n_during":1089,"n_pre":1009,"service":"checkoutservice"},{"change_pct":7.7,"n_during":363,"n_pre":337,"service":"emailservice"},{"change_pct":7.7,"n_during":726,"n_pre":674,"service":"paymentservice"},{"change_pct":4.1,"n_during":5614,"n_pre":5394,"service":"shippingservice"},{"change_pct":2.7,"n_during":9373,"n_pre":9127,"service":"cartservice"},{"change_pct":2.4,"n_during":32259,"n_pre":31498,"service":"frontend"},{"change_pct":2.0,"n_during":6802,"n_pre":6671,"service":"recommendationservice"}],"mode":"volume","omitted_services":2,"service_count":10}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":638.4,"error_pct":0.0,"p95_during_ms":763.4329999999942,"p95_pre_ms":103.38974999999996,"service":"checkoutservice","spans":9535},{"delta_pct":45.4,"error_pct":0.0,"p95_during_ms":0.6515999999999977,"p95_pre_ms":0.44820000000000004,"service":"emailservice","spans":1276},{"delta_pct":-15.3,"error_pct":0.0,"p95_during_ms":0.3336,"p95_pre_ms":0.394,"service":"paymentservice","spans":988},{"delta_pct":1.7,"error_pct":0.0,"p95_during_ms":81.55629999999992,"p95_pre_ms":80.1994,"service":"frontend","spans":206713},{"delta_pct":-1.0,"error_pct":0.0,"p95_during_ms":5.067599999999999,"p95_pre_ms":5.120849999999999,"service":"recommendationservice","spans":27522},{"delta_pct":-0.8,"error_pct":0.0,"p95_during_ms":0.234,"p95_pre_ms":0.236,"service":"currencyservice","spans":56684},{"delta_pct":0.0,"error_pct":0.0,"p95_during_ms":0.025,"p95_pre_ms":0.025,"service":"productcatalogservice","spans":103199}],"omitted_services":0,"service_count":7}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=3 omitted_edges=0
[{"evidence_source":"trace","onset_rel_s":735.0,"rank":1,"service":"checkoutservice","severity_z":155.353},{"evidence_source":"metric","onset_rel_s":801.0,"rank":2,"service":"gke-gke-cluster-default-pool-2e1807ce-0e4z","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":828.0,"rank":3,"service":"cartservice","severity_z":212.911},{"evidence_source":"trace","onset_rel_s":855.0,"rank":4,"service":"paymentservice","severity_z":45.414},{"evidence_source":"metric","onset_rel_s":1033.2,"rank":5,"service":"redis","severity_z":15.482},{"evidence_source":"metric","onset_rel_s":1093.2,"rank":6,"service":"gke-gke-cluster-default-pool-2e1807ce-xte3","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1128.0,"rank":7,"service":"shippingservice","severity_z":289.156},{"evidence_source":"metric","onset_rel_s":1213.8,"rank":8,"service":"frontend","severity_z":257.143},{"evidence_source":"metric","onset_rel_s":1261.2,"rank":9,"service":"currencyservice","severity_z":117.752},{"evidence_source":"metric","onset_rel_s":1291.8,"rank":10,"service":"gke-gke-cluster-default-pool-2e1807ce-w819","severity_z":999.0},{"evidence_source":"trace","onset_rel_s":1305.0,"rank":11,"service":"emailservice","severity_z":6.996},{"evidence_source":"metric","onset_rel_s":1360.8,"rank":12,"service":"adservice","severity_z":17.69},{"evidence_source":"none","onset_rel_s":null,"rank":13,"service":"gke-gke-cluster-default-pool-2e1807ce-cx8g","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":14,"service":"frontend-external","severity_z":0.0}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"currencyservice","caller":"checkoutservice"},{"callee":"emailservice","caller":"checkoutservice"},{"callee":"paymentservice","caller":"checkoutservice"},{"callee":"checkoutservice","caller":"frontend"},{"callee":"currencyservice","caller":"frontend"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

{"confidence":"high","reason":"Rank checkoutservice first because checkoutservice has direct container-memory-failures-total evidence (signed-z 999, persistence 32 bins); although frontend is salient, the caller path frontend -> checkoutservice means a disturbance in the callee can propagate back toward that caller-side symptom.","services":["checkoutservice","frontend"]}

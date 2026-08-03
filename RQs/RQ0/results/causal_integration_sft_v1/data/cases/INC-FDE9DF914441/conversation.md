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
opaque_id: INC-FDE9DF914441
observation_window={"duration_rel_s":1440.0,"source_metric_rows":1441}
selection_summary={"candidate_count":17,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":266,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["adservice","cartservice","checkoutservice","currencyservice","emailservice","frontend","frontend-external","gke-gke-cluster-default-pool-2e1807ce-0e4z","gke-gke-cluster-default-pool-2e1807ce-cx8g","gke-gke-cluster-default-pool-2e1807ce-w819","gke-gke-cluster-default-pool-2e1807ce-xte3","loadgenerator","paymentservice","productcatalogservice","recommendationservice","redis","shippingservice"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[11.25,33.75,56.25,78.75,101.25,123.75,146.25,168.75,191.25,213.75,236.25,258.75,281.25,303.75,326.25,348.75,371.25,393.75,416.25,438.75,461.25,483.75,506.25,528.75,551.25,573.75,596.25,618.75,641.25,663.75,686.25,708.75,731.25,753.75,776.25,798.75,821.25,843.75,866.25,888.75,911.25,933.75,956.25,978.75,1001.25,1023.75,1046.25,1068.75,1091.25,1113.75,1136.25,1158.75,1181.25,1203.75,1226.25,1248.75,1271.25,1293.75,1316.25,1338.75,1361.25,1383.75,1406.25,1428.75]
[M1] rank=1 service=emailservice metric=container-cpu-system-seconds-total baseline=0.069244 peak=13.736176 signed_z=999.0 onset_bin=32 onset_rel_s=731.25 persistence_bins=32
values_compact=delta:0.058501,0.021947,-0.000591,-0.01427,0.011259,0.007329,-0.0018,0.017543,-0.00625,-0.040443,0.02252,-0.027577,0.013603,-0.010063,-0.009667,0.036034,-0.012708,0.01269,-0.003871,-0.005248,-0.002863,0.002343,0.00854,0.001504,-0.00635,-0.011812,-0.000499,0.009103,-0.003887,0.012337,-0.008707,-0.006271,1.394481,3.7791,7.779605,0.237684,-1.961194,1.460254,-2.551388,1.836206,1.089887,-0.15984,0.27411,-0.309921,-0.361013,0.297067,0.335273,-0.178975,-0.008077,-0.069621,0.322714,-2.720747,2.507899,-0.169637,0.195387,0.203992,-0.036593,-0.162013,-2.408301,2.438608,-0.103037,-0.044685,0.48562,-0.067083
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,20,23,22,23,22,23,22,23,22,23,23
[M2] rank=2 service=emailservice metric=container-memory-failures-total baseline=0.042469 peak=148.391836 signed_z=999.0 onset_bin=32 onset_rel_s=731.25 persistence_bins=8
values_compact=raw:[0.0,0.0,0.0,0.123558,0.214486,0.08361,0.089399,0.135845,0.044048,0.0,0.047784,0.089894,0.044979,0.0,0.0,0.0,0.053673,0.038522,0.0,0.046548,0.045392,0.0,0.0,0.0,0.0,0.0,0.104392,0.040272,0.0,0.0,0.069742,0.101033,83.981056,105.511775,0.081243,0.157437,0.112381,0.0,0.441735,0.517685,0.138166,0.122406,0.042116,0.017497,0.0,0.0,0.0,0.0,0.0,0.0,0.533903,0.603514,0.060397,0.069602,0.044065,0.0,0.0,0.054326,0.100573,0.042798,0.0,0.363083,0.428868,0.048518]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,20,23,22,23,22,23,22,23,22,23,23
[M3] rank=3 service=emailservice metric=container-memory-mapped-file baseline=0.0 peak=2293760.0 signed_z=999.0 onset_bin=32 onset_rel_s=731.25 persistence_bins=32
values_compact=rle:0*32,2293760*32
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M4] rank=4 service=emailservice metric=container-memory-usage-bytes baseline=43098777.6 peak=134217728.0 signed_z=999.0 onset_bin=8 onset_rel_s=191.25 persistence_bins=34
values_compact=delta:43057152,0,8192,4096,8192,0,4096,8192,131072,0,-131072,6144,2048,-4096,4096,-4096,8192,-4096,4096,4096,0,0,0,0,-4096,4096,-4096,4096,-4096,0,8192,0,91013120,86016,-106496,77824,-12288,-20480,61440,-45056,-811008,847872,-106496,-131072,81920,155648,8192,-65536,65536,-122880,122880,0,-61440,36864,-12288,-16384,-57344,90112,-135168,155648,8192,-53248,53248,-45056
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M5] rank=5 service=gke-gke-cluster-default-pool-2e1807ce-cx8g metric=node-disk-reads-completed-total baseline=0.0 peak=0.022222 signed_z=999.0 onset_bin=45 onset_rel_s=1023.75 persistence_bins=2
values_compact=rle:0*45,0.022222*2,0*17
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M6] rank=6 service=gke-gke-cluster-default-pool-2e1807ce-w819 metric=node-disk-reads-completed-total baseline=0.0 peak=487.911111 signed_z=999.0 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,181.955556,182.133333,0.111111,6.311111,-6.422222,93.933333,-93.933333,78.977778,-23.288889,-52.955556,99.844445,-102.555556,23.777778,-12.866667,-10.933333,116.422222,-99.066667,37.333334,59.155555,-113.8,50.844445,-32.977778,-17.911111,94.6,-80.6,55.511111,28.488889,-97.977778,70.022222,-53.533333,-16.511111
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M7] rank=7 service=gke-gke-cluster-default-pool-2e1807ce-cx8g metric=node-disk-read-bytes-total baseline=0.0 peak=1547.377778 signed_z=999.0 onset_bin=45 onset_rel_s=1023.75 persistence_bins=2
values_compact=rle:0*45,1547.377778*2,0*17
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M8] rank=8 service=gke-gke-cluster-default-pool-2e1807ce-w819 metric=node-disk-read-bytes-total baseline=0.0 peak=63948572.444444 signed_z=999.0 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,23849278.577778,23872580.266666,11650.844445,827209.955555,-838860.8,12312029.866667,-12312029.866667,10351775.288889,-3052521.244444,-6940990.577778,13086811.022222,-13445074.488889,3116600.888889,-1683547.022222,-1433053.866667,15259693.511112,-12984866.133334,4893354.666667,7753636.977778,-14921910.044445,6664283.022222,-4316546.844444,-2347645.155556,12399411.2,-10564403.2,7275952.355556,3734095.644444,-12842143.288888,9177952.711111,-7016721.066667,-2164144.355556
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M9] rank=9 service=gke-gke-cluster-default-pool-2e1807ce-w819 metric=node-disk-written-bytes-total baseline=987220.574815 peak=58504533.333333 signed_z=999.0 onset_bin=32 onset_rel_s=731.25 persistence_bins=32
values_compact=delta:1014806.755556,-48969.955556,-12014.933333,41506.133333,7281.777778,-40049.777778,18477.511111,41597.155556,-4369.066667,-38138.311111,-13744.355556,-8192,33405.155556,22300.444444,-29673.244444,-36499.911111,25395.2,42507.377778,-31584.711112,-36864,16748.088889,54795.377778,-14745.6,-52246.755555,21572.266666,60256.711111,-5643.377777,-55614.577778,-15928.888889,66355.2,9375.288889,-69540.977778,10315548.444444,13647052.8,30107329.422223,1080251.733333,-451834.311111,124609.422222,-6451837.155555,5922087.822222,-4996300.8,1707030.755555,3297097.955556,-6477141.333333,6701784.177777,-786067.911111,1647593.244445,720258.844444,-6487153.777778,6162022.4,-1746807.466666,-4320824.888889,6362635.377778,-2946844.444445,1787130.311111,1857581.511111,-6455660.088889,4556026.311112,-1999394.133334,-2297764.977778,5625992.533334,-3583271.822222,4142148.266666,778695.111111
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M10] rank=10 service=emailservice metric=istio-latency-95 baseline=0.004814 peak=0.03625 signed_z=928.041 onset_bin=32 onset_rel_s=731.25 persistence_bins=32
values_compact=delta:0.004909,-0.000109,0,0,0,0,0,0,0,0,0,0,0,0,0,0.00009,-0.000002,-0.000088,0,0,0,0.000086,0.000004,-0.00009,0,0,0,0,0,0,0,0,0.00195,0.011875,0.003804,0.000696,0.001534,0.011591,-0.012,-0.000402,-0.00048,-0.00033,0.000516,0.000368,-0.000146,-0.000006,-0.000103,-0.000849,0.000007,0.000362,0.001476,-0.000194,-0.00079,0.000026,-0.000247,0.000121,0.000126,-0.000025,0.000295,0.000053,-0.000486,0.000271,0.000159,-0.000258
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M11] rank=11 service=emailservice metric=istio-latency-50 baseline=0.003007 peak=0.015625 signed_z=707.735 onset_bin=32 onset_rel_s=731.25 persistence_bins=32
values_compact=delta:0.003057,-0.000057,0,0,0,0,0,0,0,0,0,0,0,0,0,0.000048,-0.000001,-0.000047,0,0,0,0.000045,0.000003,-0.000048,0,0,0,0,0,0,0,0,0.000129,0.000486,0.002814,0.001785,-0.000089,-0.001875,0.004934,0.002298,-0.008587,-0.000117,0.005758,0.003683,-0.001456,-0.000063,-0.001033,-0.007088,0.000186,0.003152,-0.001042,0.0025,0.002411,0.000259,-0.003295,0.002039,0.001256,-0.000245,0.00295,0.000528,-0.004861,0.002708,0.001597,-0.002579
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M12] rank=12 service=emailservice metric=istio-latency-90 baseline=0.004613 peak=0.0235 signed_z=588.542 onset_bin=32 onset_rel_s=731.25 persistence_bins=32
values_compact=delta:0.004703,-0.000103,0,0,0,0,0,0,0,0,0,0,0,0,0,0.000086,-0.000002,-0.000084,0,0,0,0.000082,0.000004,-0.000086,0,0,0,0,0,0,0,0,0.000232,0.007418,0.007607,0.001393,0.001705,0.000212,-0.000381,-0.00009,-0.000961,-0.000658,0.00103,0.000737,-0.000291,-0.000013,-0.000207,-0.001697,0.000014,0.000725,0.00145,0.00005,-0.000518,0.000052,-0.000492,0.000241,0.000251,-0.000049,0.00059,0.000106,-0.000973,0.000542,0.000319,-0.000515
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[702.0,1440.0]

=== LOG SUMMARY ===
{"entries":[{"change_pct":50.0,"n_during":15,"n_pre":10,"service":"redis"},{"change_pct":6.3,"n_during":5272,"n_pre":4958,"service":"adservice"},{"change_pct":4.9,"n_during":30952,"n_pre":29493,"service":"frontend"},{"change_pct":4.8,"n_during":27847,"n_pre":26584,"service":"currencyservice"},{"change_pct":4.8,"n_during":6522,"n_pre":6223,"service":"recommendationservice"},{"change_pct":4.5,"n_during":8909,"n_pre":8529,"service":"cartservice"},{"change_pct":-3.1,"n_during":893,"n_pre":922,"service":"checkoutservice"},{"change_pct":-2.9,"n_during":298,"n_pre":307,"service":"emailservice"}],"mode":"volume","omitted_services":2,"service_count":10}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":220.6,"error_pct":0.0,"p95_during_ms":1.390049999999998,"p95_pre_ms":0.43360000000000026,"service":"emailservice","spans":1181},{"delta_pct":4.7,"error_pct":0.0,"p95_during_ms":222.46484999999998,"p95_pre_ms":212.50939999999997,"service":"checkoutservice","spans":8472},{"delta_pct":4.2,"error_pct":0.0,"p95_during_ms":0.5495000000000001,"p95_pre_ms":0.5273999999999998,"service":"paymentservice","spans":893},{"delta_pct":-3.1,"error_pct":0.0,"p95_during_ms":192.346,"p95_pre_ms":198.51914999999983,"service":"frontend","spans":197505},{"delta_pct":-1.7,"error_pct":0.0,"p95_during_ms":0.177,"p95_pre_ms":0.18,"service":"currencyservice","spans":54717},{"delta_pct":0.2,"error_pct":0.0,"p95_during_ms":5.130049999999999,"p95_pre_ms":5.11775,"service":"recommendationservice","spans":26066},{"delta_pct":0.0,"error_pct":0.0,"p95_during_ms":0.024,"p95_pre_ms":0.024,"service":"productcatalogservice","spans":98200}],"omitted_services":0,"service_count":7}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=3 omitted_edges=0
[{"evidence_source":"trace","onset_rel_s":735.0,"rank":1,"service":"emailservice","severity_z":175.546},{"evidence_source":"trace","onset_rel_s":735.0,"rank":2,"service":"paymentservice","severity_z":6.775},{"evidence_source":"metric","onset_rel_s":772.2,"rank":3,"service":"gke-gke-cluster-default-pool-2e1807ce-w819","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1020.0,"rank":4,"service":"gke-gke-cluster-default-pool-2e1807ce-cx8g","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1395.0,"rank":5,"service":"checkoutservice","severity_z":19.963},{"evidence_source":"metric","onset_rel_s":1401.0,"rank":6,"service":"gke-gke-cluster-default-pool-2e1807ce-xte3","severity_z":16.53},{"evidence_source":"none","onset_rel_s":null,"rank":7,"service":"adservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":8,"service":"redis","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":9,"service":"recommendationservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":10,"service":"loadgenerator","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":11,"service":"productcatalogservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":12,"service":"gke-gke-cluster-default-pool-2e1807ce-0e4z","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":13,"service":"cartservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":14,"service":"currencyservice","severity_z":0.0}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"currencyservice","caller":"checkoutservice"},{"callee":"emailservice","caller":"checkoutservice"},{"callee":"paymentservice","caller":"checkoutservice"},{"callee":"productcatalogservice","caller":"checkoutservice"},{"callee":"productcatalogservice","caller":"recommendationservice"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

{"confidence":"high","reason":"Rank emailservice first because emailservice has direct container-cpu-system-seconds-total evidence (signed-z 999, persistence 32 bins); although checkoutservice is salient, the caller path checkoutservice -> emailservice means a disturbance in the callee can propagate back toward that caller-side symptom.","services":["emailservice","checkoutservice"]}

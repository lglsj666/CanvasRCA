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
opaque_id: INC-9A7655425187
observation_window={"duration_rel_s":1440.0,"source_metric_rows":1441}
selection_summary={"candidate_count":16,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":257,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["adservice","cartservice","checkoutservice","currencyservice","emailservice","frontend","frontend-external","gke-gke-cluster-default-pool-2e1807ce-0e4z","gke-gke-cluster-default-pool-2e1807ce-cx8g","gke-gke-cluster-default-pool-2e1807ce-w819","loadgenerator","paymentservice","productcatalogservice","recommendationservice","redis","shippingservice"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[11.25,33.75,56.25,78.75,101.25,123.75,146.25,168.75,191.25,213.75,236.25,258.75,281.25,303.75,326.25,348.75,371.25,393.75,416.25,438.75,461.25,483.75,506.25,528.75,551.25,573.75,596.25,618.75,641.25,663.75,686.25,708.75,731.25,753.75,776.25,798.75,821.25,843.75,866.25,888.75,911.25,933.75,956.25,978.75,1001.25,1023.75,1046.25,1068.75,1091.25,1113.75,1136.25,1158.75,1181.25,1203.75,1226.25,1248.75,1271.25,1293.75,1316.25,1338.75,1361.25,1383.75,1406.25,1428.75]
[M1] rank=1 service=emailservice metric=container-memory-failures-total baseline=0.041542 peak=701.46778 signed_z=999.0 onset_bin=32 onset_rel_s=731.25 persistence_bins=14
values_compact=rle:0.275065*1,0.267415*1,0*4,0.044647*1,0.041483*1,0*3,0.151903*1,0.185964*1,0*10,0.272957*1,0.31369*1,0.046541*1,0*6,32.033461*1,35.844369*1,0.240427*1,0.256816*1,0*5,447.219224*1,454.931866*1,0.802676*1,0.3*1,0.376294*1,0.4*1,0.39548*1,496.633454*1,420.295822*1,0.61561*1,0.24534*1,0.13395*1,0.137033*1,0.06401*1,0.049861*1,0.048151*1,0*2,0.428294*1,0.602345*1,0.335086*1,0.119334*1,0*1
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,18,23,22,23,23
[M2] rank=2 service=emailservice metric=container-memory-rss baseline=40942768.355556 peak=122077184.0 signed_z=999.0 onset_bin=40 onset_rel_s=911.25 persistence_bins=24
values_compact=delta:40939520,0,0,0,0,0,4096,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,-4096,4096,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,2170880,38240256,61440,24576,0,28672,8192,1867776,38653952,43008,22528,0,12288,-40939520,0,0,4096,0,0,40505344,-40534016,12288,0,1863680
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M3] rank=3 service=emailservice metric=container-memory-usage-bytes baseline=43759627.377778 peak=130121728.0 signed_z=999.0 onset_bin=40 onset_rel_s=911.25 persistence_bins=24
values_compact=delta:43757568,-4096,4096,-4096,0,4096,0,0,0,4096,0,0,0,4096,0,0,-8192,0,4096,0,4096,-4096,-4096,-4096,4096,0,0,0,0,4096,0,0,4096,-8192,8192,-2048,-2048,0,-4096,8192,2740224,40296448,61440,20480,0,28672,8192,2437120,40685568,45056,20480,4096,8192,-43753472,0,4096,0,0,0,43044864,-43167744,12288,0,2416640
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M4] rank=4 service=emailservice metric=container-memory-working-set-bytes baseline=43685899.377778 peak=129900544.0 signed_z=999.0 onset_bin=40 onset_rel_s=911.25 persistence_bins=24
values_compact=delta:43683840,-4096,4096,-4096,0,4096,0,0,0,4096,0,0,0,4096,0,0,-8192,0,4096,0,4096,-4096,-4096,-4096,4096,0,0,0,0,4096,0,0,4096,-8192,8192,-2048,-2048,0,-4096,8192,2740224,40222720,61440,20480,0,28672,8192,2437120,40611840,45056,20480,4096,8192,-43679744,0,4096,0,0,0,42971136,-43094016,12288,0,2416640
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M5] rank=5 service=emailservice metric=istio-latency-90 baseline=0.004645 peak=0.549433 signed_z=999.0 onset_bin=34 onset_rel_s=776.25 persistence_bins=29
values_compact=delta:0.0046,0,0,0,0,0.000124,0.000009,0.000144,-0.000071,-0.000206,0,0,0,0,0.00009,-0.00001,-0.00008,0,0,0.000084,-0.000006,-0.000078,0.000106,0.00001,-0.000116,0,0,0,0.000065,0,-0.000065,0,0,0.00024,0.15516,0.042,-0.045,-0.102,0.06,-0.110182,0.070182,0.065,-0.007602,0.012602,-0.012,0.07575,0.01625,-0.220062,0.006562,0.197932,-0.016932,0.006071,0.001429,-0.005,0,0.0175,0.013022,-0.041727,0.078705,0.087819,-0.127819,-0.036786,-0.177214,-0.0015
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M6] rank=6 service=emailservice metric=istio-latency-95 baseline=0.004906 peak=0.774717 signed_z=999.0 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=delta:0.0048,0,0,0,0,0.000131,0.00001,0.001559,-0.001125,-0.000575,0,0,0,0,0.000095,-0.000011,-0.000084,0,0,0.000088,-0.000005,-0.000083,0.000112,0.000011,-0.000123,0,0,0,0.000069,0,-0.000069,0,0,0.1552,0.44,-0.175,-0.1915,-0.056,0.055,-0.095,0.105,0.0025,-0.053801,0.006301,-0.006,0.171,0.075,-0.375,0.045,0.233694,-0.094944,0.07875,0.3,0.05625,-0.43125,0,0.13676,-0.154862,0.211852,0.156569,-0.231569,-0.140179,-0.064821,-0.01875
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M7] rank=7 service=emailservice metric=istio-latency-99 baseline=0.006146 peak=1.915 signed_z=999.0 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=delta:0.00496,0,0,0,0,0.00354,0.0001,0.0007,-0.000225,-0.004115,0,0,0,0,0.00299,-0.00025,-0.00274,0,0,0.00284,-0.00015,-0.00269,0.00329,0.00015,-0.00344,0,0,0,0.00224,0,-0.00224,0,0,0.83504,0.08,0.89,-0.075,-1.35,0.05625,-0.02875,0.3825,-0.005,-0.55176,0.00126,-0.0012,0.6067,0.03,-0.6775,0.205,0.065739,-0.021989,0.41875,0.06,0.01125,-0.03625,-0.1,0.054704,-0.434875,0.435171,0.065064,-0.125064,-0.395,-0.16725,-0.00375
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M8] rank=8 service=emailservice metric=container-memory-cache baseline=163840.0 peak=454656.0 signed_z=272.248 onset_bin=40 onset_rel_s=911.25 persistence_bins=24
values_compact=rle:163840*40,188416*1,327680*6,348160*1,454656*5,290816*6,364544*1,200704*4
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M9] rank=9 service=productcatalogservice metric=istio-latency-99 baseline=0.00497 peak=0.00754 signed_z=192.694 onset_bin=45 onset_rel_s=1023.75 persistence_bins=3
values_compact=delta:0.004996,-0.000001,-0.000018,0.000006,0,-0.000016,-0.000002,-0.000008,0.000001,0.000008,-0.000003,-0.000014,0.000019,0.000028,-0.00001,-0.000018,0.000003,0.00002,-0.000013,-0.000021,0.000002,0.000006,0.000001,-0.000009,-0.000009,0.000004,0.000007,0.000026,0.000002,-0.000018,-0.00001,0.000005,0.000001,0.000016,0.000004,-0.000016,-0.00001,0.000019,0.000001,-0.000019,0.000001,0.000001,0.000001,0.000006,0.000011,0.001413,0.000371,-0.001393,-0.000381,-0.000023,0.000004,-0.000004,0,-0.000009,0,0.000001,0.000002,0.000011,-0.000002,-0.000005,-0.000002,0,0.000006,-0.000002
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M10] rank=10 service=shippingservice metric=istio-latency-99 baseline=0.004963 peak=0.006075 signed_z=141.628 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.004981,-0.000013,-0.000012,0.000001,0,0,0.000001,0,-0.000001,0.000013,0.000001,-0.000001,-0.000001,-0.000012,0.000023,0.000001,-0.000023,0.000001,0,-0.000001,0,-0.000001,0,0.000014,-0.000001,-0.000011,0,-0.000002,0,0.000001,0.000001,-0.000001,-0.000001,0,0.000001,0.000012,0,-0.000012,0,0,0,-0.000002,0,0.000001,0.000001,0.000001,0,-0.000001,0,0.000001,-0.000001,0.000001,0.00001,0.000021,-0.00001,0.000003,0.000001,-0.000026,0.000001,-0.000001,0,0,0,0.000012
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M11] rank=11 service=emailservice metric=container-network-receive-bytes-total baseline=798.817312 peak=10438.197677 signed_z=80.422 onset_bin=34 onset_rel_s=776.25 persistence_bins=27
values_compact=delta:1056.38368,-112.229352,-54.915561,-111.30386,-7.889117,-41.808238,-73.613317,0.163365,17.638767,115.378328,-26.850949,114.83772,-2.411693,-115.913476,42.79955,131.547303,-25.442826,-109.691215,-107.890715,156.547661,1.370904,102.433197,-198.01546,-51.187142,91.408081,-7.328469,24.361176,118.597113,0,-22.681711,-5.856011,-62.23333,-64.155975,149.914166,5203.76362,-949.970545,896.187791,-399.073228,-4424.652689,-124.962347,5.448445,4669.181904,-830.127061,-3867.212563,189.236066,5395.524971,2819.608181,-3142.707513,1181.724647,-2082.943909,294.916455,-127.08584,-4184.025551,110.91834,-389.084339,31.570055,57.809664,130.839504,-4.828592,4375.020662,-4448.776852,0,157.070645,-244.066013
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M12] rank=12 service=emailservice metric=container-cpu-user-seconds-total baseline=0.211317 peak=2.117303 signed_z=70.8 onset_bin=41 onset_rel_s=933.75 persistence_bins=5
values_compact=raw:[0.249853,0.229957,0.208398,0.203718,0.188806,0.188696,0.191903,0.189055,0.199032,0.209216,0.218081,0.224567,0.218011,0.214408,0.222917,0.227115,0.2422,0.212199,0.2277,0.224247,0.221361,0.212629,0.200753,0.208205,0.233368,0.239204,0.2146,0.215342,0.243653,0.256231,0.223232,0.219478,0.227181,0.213091,0.190265,0.188604,0.223424,0.2258,0.232374,0.205201,0.185355,1.454988,1.433929,0.240112,0.246155,0.239766,0.150918,0.233556,1.52301,1.398015,0.270508,0.26632,0.281272,0.289522,0.233759,0.214124,0.239404,0.152395,0.136125,0.123795,0.229114,0.271666,0.262855,0.166159]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,18,23,22,23,23

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[902.0,1440.0]

=== LOG SUMMARY ===
{"entries":[{"error_logs":18,"error_pct":0.92,"service":"checkoutservice","total_logs":1962}],"mode":"errors","omitted_services":9,"service_count":10}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":66.4,"error_pct":0.0,"p95_during_ms":133.91394999999957,"p95_pre_ms":80.47889999999988,"service":"checkoutservice","spans":9132},{"delta_pct":-23.4,"error_pct":0.0,"p95_during_ms":0.32434999999999997,"p95_pre_ms":0.4235499999999999,"service":"paymentservice","spans":942},{"delta_pct":5.9,"error_pct":0.0,"p95_during_ms":0.4465,"p95_pre_ms":0.4216999999999999,"service":"emailservice","spans":1113},{"delta_pct":3.6,"error_pct":0.0,"p95_during_ms":0.029,"p95_pre_ms":0.028,"service":"productcatalogservice","spans":104230},{"delta_pct":-2.5,"error_pct":0.0,"p95_during_ms":64.2704,"p95_pre_ms":65.9118,"service":"frontend","spans":209252},{"delta_pct":0.8,"error_pct":0.0,"p95_during_ms":0.248,"p95_pre_ms":0.246,"service":"currencyservice","spans":57712},{"delta_pct":0.8,"error_pct":0.0,"p95_during_ms":5.35925,"p95_pre_ms":5.3157499999999995,"service":"recommendationservice","spans":27682}],"omitted_services":0,"service_count":7}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=2 omitted_edges=0
[{"evidence_source":"metric","onset_rel_s":850.8,"rank":1,"service":"cartservice","severity_z":11.338},{"evidence_source":"metric","onset_rel_s":925.8,"rank":2,"service":"emailservice","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1023.0,"rank":3,"service":"productcatalogservice","severity_z":192.694},{"evidence_source":"metric","onset_rel_s":1053.0,"rank":4,"service":"frontend","severity_z":11.218},{"evidence_source":"trace","onset_rel_s":1215.0,"rank":5,"service":"checkoutservice","severity_z":8.048},{"evidence_source":"metric","onset_rel_s":1243.8,"rank":6,"service":"shippingservice","severity_z":141.628},{"evidence_source":"metric","onset_rel_s":1404.0,"rank":7,"service":"adservice","severity_z":11.662},{"evidence_source":"none","onset_rel_s":null,"rank":8,"service":"gke-gke-cluster-default-pool-2e1807ce-w819","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":9,"service":"gke-gke-cluster-default-pool-2e1807ce-cx8g","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":10,"service":"redis","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":11,"service":"gke-gke-cluster-default-pool-2e1807ce-0e4z","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":12,"service":"paymentservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":13,"service":"recommendationservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":14,"service":"currencyservice","severity_z":0.0}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"currencyservice","caller":"checkoutservice"},{"callee":"emailservice","caller":"checkoutservice"},{"callee":"paymentservice","caller":"checkoutservice"},{"callee":"productcatalogservice","caller":"checkoutservice"},{"callee":"checkoutservice","caller":"frontend"},{"callee":"currencyservice","caller":"frontend"},{"callee":"productcatalogservice","caller":"frontend"},{"callee":"recommendationservice","caller":"frontend"},{"callee":"productcatalogservice","caller":"recommendationservice"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

{"confidence":"high","reason":"Rank emailservice first because emailservice has direct container-memory-failures-total evidence (signed-z 999, persistence 14 bins); although checkoutservice is salient, the caller path checkoutservice -> emailservice means a disturbance in the callee can propagate back toward that caller-side symptom.","services":["emailservice","checkoutservice"]}

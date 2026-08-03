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
opaque_id: INC-4193AFA8ACDB
observation_window={"duration_rel_s":1440.0,"source_metric_rows":1441}
selection_summary={"candidate_count":17,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":265,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["adservice","cartservice","checkoutservice","currencyservice","emailservice","frontend","frontend-external","gke-gke-cluster-default-pool-2e1807ce-0e4z","gke-gke-cluster-default-pool-2e1807ce-cx8g","gke-gke-cluster-default-pool-2e1807ce-w819","gke-gke-cluster-default-pool-2e1807ce-xte3","loadgenerator","paymentservice","productcatalogservice","recommendationservice","redis","shippingservice"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[11.25,33.75,56.25,78.75,101.25,123.75,146.25,168.75,191.25,213.75,236.25,258.75,281.25,303.75,326.25,348.75,371.25,393.75,416.25,438.75,461.25,483.75,506.25,528.75,551.25,573.75,596.25,618.75,641.25,663.75,686.25,708.75,731.25,753.75,776.25,798.75,821.25,843.75,866.25,888.75,911.25,933.75,956.25,978.75,1001.25,1023.75,1046.25,1068.75,1091.25,1113.75,1136.25,1158.75,1181.25,1203.75,1226.25,1248.75,1271.25,1293.75,1316.25,1338.75,1361.25,1383.75,1406.25,1428.75]
[M1] rank=1 service=checkoutservice metric=container-memory-failures-total baseline=3.267936 peak=41746.209141 signed_z=999.0 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=delta:6.602555,-2.185732,-1.611396,0.763365,-1.128329,2.204351,1.734771,-3.062395,-0.44322,0.532194,-0.094401,-2.089836,2.842577,-0.794495,1.553974,1.604192,-1.690691,-3.383356,-0.527286,0.832122,0.47893,-0.84775,-0.77319,0.758104,-0.002823,2.827342,0.905804,-4.119049,-0.34889,5.230339,0.601646,-2.551876,-0.083836,18943.237724,19398.717319,2746.513996,-1516.203264,167.992681,161.324478,-155.946725,-801.845397,-1497.500712,2060.184912,-9934.827743,11654.380364,-3705.537004,877.784739,1855.435944,698.194904,-754.507399,-1059.170989,508.930127,132.325915,445.006182,-751.071913,1065.55617,-7206.324158,6237.749696,819.211818,281.648346,-1173.473522,741.120561,-607.433268,-798.337249
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M2] rank=2 service=gke-gke-cluster-default-pool-2e1807ce-w819 metric=node-memory-active-bytes baseline=1474.939259 peak=22019185.777778 signed_z=999.0 onset_bin=40 onset_rel_s=911.25 persistence_bins=4
values_compact=delta:1638.4,-273.066667,-91.022222,182.044445,273.066666,-364.088889,-546.133333,182.044444,0,546.133334,728.177778,-455.111112,-728.177777,-91.022223,364.088889,364.088889,-273.066666,-455.111112,364.088889,455.111111,273.066667,182.044445,-455.111112,-273.066666,-91.022222,-364.088889,273.066666,91.022223,91.022222,-91.022222,0,273.066666,182.044445,-273.066667,-182.044444,0,-273.066667,546.133333,273.066667,-182.044445,910.222223,-182.044445,-1001.244444,0,182.044444,0,0,0,-364.088889,-455.111111,182.044445,0,22017729.422222,364.088889,-22018457.6,-91.022222,1092.266666,0,-1092.266666,182.044444,1001.244444,-273.066666,0,91.022222
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M3] rank=3 service=checkoutservice metric=container-memory-working-set-bytes baseline=10769174.755556 peak=268439552.0 signed_z=955.7 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=delta:10989568,-569344,188416,147456,-430080,348160,-401408,208896,69632,262144,32768,-294912,311296,145408,-428032,200704,-237568,51200,22528,90112,106496,0,40960,98304,4096,376832,20480,-745472,4096,385024,348160,-405504,0,257495040,0,0,-12288,12288,4096,-4096,0,-41295872,41275392,-101072896,76828672,-96755712,121024512,-4096,0,2048,-2048,-96819200,96819200,-104443904,104443904,2048,2048,-4096,0,0,4096,-6144,-180402176,180404224
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M4] rank=4 service=checkoutservice metric=container-memory-usage-bytes baseline=11059990.755556 peak=268439552.0 signed_z=954.621 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=delta:11280384,-569344,188416,147456,-430080,348160,-401408,208896,69632,262144,32768,-294912,311296,145408,-428032,200704,-237568,51200,22528,90112,106496,0,40960,98304,4096,376832,20480,-745472,4096,385024,348160,-405504,0,257204224,0,0,-12288,12288,4096,-4096,0,-41295872,41275392,-101072896,76828672,-96755712,121024512,-4096,0,2048,-2048,-96819200,96819200,-104443904,104443904,2048,2048,-4096,0,0,4096,-6144,-180402176,180404224
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M5] rank=5 service=checkoutservice metric=container-memory-rss baseline=10257538.844444 peak=264916992.0 signed_z=944.858 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=delta:10469376,-552960,184320,151552,-458752,376832,-401408,208896,69632,262144,28672,-294912,286720,155648,-430080,212992,-233472,36864,36864,90112,102400,0,45056,98304,4096,376832,20480,-749568,8192,385024,348160,-405504,0,254484480,-24576,0,-8192,12288,-4096,4096,0,-41504768,41480192,-100872192,76677120,-96575488,120795136,0,0,0,0,-96653312,96653312,-104239104,104239104,-4096,0,4096,0,0,0,-4096,-180068352,180072448
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M6] rank=6 service=checkoutservice metric=container-memory-mapped-file baseline=126976.0 peak=2211840.0 signed_z=942.593 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=rle:126976*33,2211840*31
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M7] rank=7 service=checkoutservice metric=container-cpu-system-seconds-total baseline=0.134463 peak=16.095868 signed_z=742.316 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=delta:0.15184,-0.039799,0.009354,0.02505,0.019895,0.004734,-0.030323,-0.008459,-0.028485,0.017116,0.031897,-0.014515,0.009815,-0.02416,0.00202,0.028446,0.002962,-0.033856,0.023032,0.010416,-0.040896,0.015681,0.004128,-0.029093,0.019399,0.02845,-0.025395,-0.021596,-0.004523,0.04268,0.022997,-0.046259,0.011527,6.594716,4.255041,2.894071,0.428375,-0.155655,0.705849,0.127477,-0.292436,-0.854502,1.496369,-4.636377,4.615635,0.085833,0,0.143775,0.553617,-0.768562,-0.310827,0.243675,-0.333745,0.527746,0.352314,0.018385,-3.121751,3.197396,-0.473187,-0.030876,-0.097863,0.284448,-0.181728,-0.234675
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M8] rank=8 service=gke-gke-cluster-default-pool-2e1807ce-xte3 metric=node-disk-reads-completed-total baseline=0.0 peak=0.177778 signed_z=493.701 onset_bin=53 onset_rel_s=1203.75 persistence_bins=4
values_compact=rle:0*53,0.177778*4,0*7
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M9] rank=9 service=checkoutservice metric=container-memory-cache baseline=299008.0 peak=2211840.0 signed_z=386.648 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=rle:299008*33,2211840*31
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M10] rank=10 service=gke-gke-cluster-default-pool-2e1807ce-xte3 metric=node-disk-read-bytes-total baseline=0.0 peak=7736.888889 signed_z=328.296 onset_bin=53 onset_rel_s=1203.75 persistence_bins=4
values_compact=rle:0*53,7736.888889*2,1729.422222*2,0*7
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M11] rank=11 service=checkoutservice metric=container-cpu-usage-seconds-total baseline=0.391702 peak=20.677604 signed_z=328.248 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=delta:0.455808,-0.112476,0.02527,0.031794,-0.013721,0.018149,-0.05231,-0.009391,0.014864,0.085668,0.046632,-0.053435,-0.015099,-0.06981,0.023571,0.097132,0.00391,-0.107148,0.050719,0.054639,-0.073605,0.007753,-0.042852,-0.103124,0.046955,0.152165,0.027586,-0.126631,-0.072091,0.061768,0.095977,-0.028684,0.031671,11.225962,5.87641,2.817263,0.082014,-0.790893,0.207687,0.110697,-0.419412,-1.400289,1.88386,-5.941252,5.807639,0.055238,0,-0.124597,0.655496,-0.37517,-0.550777,0.267948,-0.527103,0.661818,0.50466,-0.097788,-3.948897,3.937476,-0.740686,0.152746,-0.211117,0.505215,-0.311499,-0.334459
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M12] rank=12 service=checkoutservice metric=container-sockets baseline=9.0 peak=12.0 signed_z=250.0 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=rle:9*33,12*31
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[718.0,1440.0]

=== LOG SUMMARY ===
{"entries":[{"change_pct":-33.3,"n_during":10,"n_pre":15,"service":"redis"},{"change_pct":3.3,"n_during":1020,"n_pre":987,"service":"checkoutservice"},{"change_pct":3.3,"n_during":340,"n_pre":329,"service":"emailservice"},{"change_pct":3.3,"n_during":680,"n_pre":658,"service":"paymentservice"},{"change_pct":-2.7,"n_during":28234,"n_pre":29005,"service":"currencyservice"},{"change_pct":1.8,"n_during":5468,"n_pre":5370,"service":"shippingservice"},{"change_pct":-1.4,"n_during":5337,"n_pre":5413,"service":"adservice"},{"change_pct":-0.9,"n_during":31833,"n_pre":32138,"service":"frontend"}],"mode":"volume","omitted_services":2,"service_count":10}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":583.5,"error_pct":0.0,"p95_during_ms":497.4565999999986,"p95_pre_ms":72.77699999999993,"service":"checkoutservice","spans":9156},{"delta_pct":11.0,"error_pct":0.0,"p95_during_ms":60.503599999999864,"p95_pre_ms":54.528,"service":"frontend","spans":208206},{"delta_pct":5.3,"error_pct":0.0,"p95_during_ms":0.219,"p95_pre_ms":0.208,"service":"currencyservice","spans":57525},{"delta_pct":-3.9,"error_pct":0.0,"p95_during_ms":0.5202999999999998,"p95_pre_ms":0.5412999999999996,"service":"emailservice","spans":1245},{"delta_pct":3.6,"error_pct":0.0,"p95_during_ms":0.53025,"p95_pre_ms":0.512,"service":"paymentservice","spans":957},{"delta_pct":-2.3,"error_pct":0.0,"p95_during_ms":4.82375,"p95_pre_ms":4.935949999999999,"service":"recommendationservice","spans":27528},{"delta_pct":0.0,"error_pct":0.0,"p95_during_ms":0.03,"p95_pre_ms":0.03,"service":"productcatalogservice","spans":103554}],"omitted_services":0,"service_count":7}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=3 omitted_edges=0
[{"evidence_source":"trace","onset_rel_s":735.0,"rank":1,"service":"checkoutservice","severity_z":227.609},{"evidence_source":"metric","onset_rel_s":802.8,"rank":2,"service":"cartservice","severity_z":119.415},{"evidence_source":"metric","onset_rel_s":942.0,"rank":3,"service":"recommendationservice","severity_z":18.143},{"evidence_source":"metric","onset_rel_s":978.0,"rank":4,"service":"paymentservice","severity_z":51.916},{"evidence_source":"metric","onset_rel_s":988.2,"rank":5,"service":"frontend","severity_z":41.667},{"evidence_source":"metric","onset_rel_s":1032.0,"rank":6,"service":"emailservice","severity_z":97.149},{"evidence_source":"metric","onset_rel_s":1035.0,"rank":7,"service":"gke-gke-cluster-default-pool-2e1807ce-cx8g","severity_z":10.822},{"evidence_source":"metric","onset_rel_s":1179.0,"rank":8,"service":"gke-gke-cluster-default-pool-2e1807ce-w819","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1183.8,"rank":9,"service":"gke-gke-cluster-default-pool-2e1807ce-xte3","severity_z":493.701},{"evidence_source":"metric","onset_rel_s":1227.0,"rank":10,"service":"shippingservice","severity_z":11.407},{"evidence_source":"metric","onset_rel_s":1281.0,"rank":11,"service":"gke-gke-cluster-default-pool-2e1807ce-0e4z","severity_z":246.495},{"evidence_source":"none","onset_rel_s":null,"rank":12,"service":"adservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":13,"service":"currencyservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":14,"service":"redis","severity_z":0.0}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"currencyservice","caller":"checkoutservice"},{"callee":"emailservice","caller":"checkoutservice"},{"callee":"paymentservice","caller":"checkoutservice"},{"callee":"checkoutservice","caller":"frontend"},{"callee":"currencyservice","caller":"frontend"},{"callee":"recommendationservice","caller":"frontend"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

{"confidence":"high","reason":"Rank checkoutservice first because checkoutservice has direct container-memory-failures-total evidence (signed-z 999, persistence 31 bins); although frontend is salient, the caller path frontend -> checkoutservice means a disturbance in the callee can propagate back toward that caller-side symptom.","services":["checkoutservice","frontend"]}

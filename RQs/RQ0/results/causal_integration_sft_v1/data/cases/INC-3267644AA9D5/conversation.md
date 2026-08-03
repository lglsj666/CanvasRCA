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
opaque_id: INC-3267644AA9D5
observation_window={"duration_rel_s":1440.0,"source_metric_rows":1441}
selection_summary={"candidate_count":17,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":269,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["adservice","cartservice","checkoutservice","currencyservice","emailservice","frontend","frontend-external","gke-gke-cluster-default-pool-2e1807ce-0e4z","gke-gke-cluster-default-pool-2e1807ce-cx8g","gke-gke-cluster-default-pool-2e1807ce-w819","gke-gke-cluster-default-pool-2e1807ce-xte3","loadgenerator","paymentservice","productcatalogservice","recommendationservice","redis","shippingservice"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[11.25,33.75,56.25,78.75,101.25,123.75,146.25,168.75,191.25,213.75,236.25,258.75,281.25,303.75,326.25,348.75,371.25,393.75,416.25,438.75,461.25,483.75,506.25,528.75,551.25,573.75,596.25,618.75,641.25,663.75,686.25,708.75,731.25,753.75,776.25,798.75,821.25,843.75,866.25,888.75,911.25,933.75,956.25,978.75,1001.25,1023.75,1046.25,1068.75,1091.25,1113.75,1136.25,1158.75,1181.25,1203.75,1226.25,1248.75,1271.25,1293.75,1316.25,1338.75,1361.25,1383.75,1406.25,1428.75]
[M1] rank=1 service=recommendationservice metric=container-memory-mapped-file baseline=0.0 peak=2293760.0 signed_z=999.0 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=rle:0*33,2293760*31
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M2] rank=2 service=recommendationservice metric=container-memory-usage-bytes baseline=44312041.244444 peak=471859200.0 signed_z=999.0 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=delta:44179456,28672,0,8192,-20480,45056,4096,4096,24576,-24576,28672,20480,0,20480,-4096,8192,8192,-8192,8192,4096,139264,-159744,32768,63488,75776,-299008,180224,-40960,94208,16384,0,32768,-12288,427163648,32768,106496,8192,0,90112,-102400,-20480,24576,-274432,274432,-98304,69632,126976,-278528,-156942336,156995584,147456,-28672,-74346496,-108679168,182996992,-102400,-123080704,123283456,-63488,-84180992,84279296,-221184,94208,-163840
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M3] rank=3 service=recommendationservice metric=istio-latency-90 baseline=0.009637 peak=0.204708 signed_z=999.0 onset_bin=32 onset_rel_s=731.25 persistence_bins=32
values_compact=raw:[0.009812,0.009708,0.009668,0.009561,0.009601,0.009605,0.009659,0.009665,0.009614,0.009581,0.009521,0.00963,0.009625,0.009688,0.009808,0.009648,0.009535,0.009512,0.009639,0.009741,0.009672,0.009687,0.009674,0.009552,0.009501,0.00951,0.00954,0.009526,0.009561,0.009808,0.009769,0.009829,0.01932,0.08,0.174056,0.194493,0.182075,0.174483,0.179358,0.1716,0.162852,0.164034,0.168859,0.17168,0.149404,0.153914,0.155645,0.180066,0.1855,0.169933,0.201678,0.196317,0.181222,0.183196,0.191974,0.195226,0.182642,0.185971,0.187711,0.183051,0.175,0.159286,0.147692,0.166691]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M4] rank=4 service=gke-gke-cluster-default-pool-2e1807ce-w819 metric=node-memory-active-bytes baseline=1918.419753 peak=10929038.222222 signed_z=999.0 onset_bin=33 onset_rel_s=753.75 persistence_bins=19
values_compact=delta:2093.511111,0,728.177778,-273.066667,-1092.266666,273.066666,91.022222,-91.022222,273.066667,455.111111,-364.088889,-819.2,546.133333,182.044445,-728.177778,91.022222,273.066667,273.066667,455.111111,-273.066667,-637.155555,0,364.088888,273.066667,-455.111111,-182.044444,910.222222,364.088889,-364.088889,-273.066667,-455.111111,-273.066667,1183.288889,1092.266667,1456.355555,-182.044444,-1729.422222,-364.088889,-364.088889,-364.088889,1092.266667,364.088889,-819.2,0,546.133333,0,-91.022222,-91.022222,10925579.377777,364.088889,-10923576.888889,-273.066666,-2093.511111,-182.044445,91.022222,455.111111,-364.088888,-455.111112,91.022223,0,-273.066667,1183.288889,455.111111,-1911.466667
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M5] rank=5 service=gke-gke-cluster-default-pool-2e1807ce-w819 metric=node-disk-written-bytes-total baseline=990059.45679 peak=54438388.622222 signed_z=999.0 onset_bin=32 onset_rel_s=731.25 persistence_bins=32
values_compact=delta:989502.577778,-38957.511111,33678.222222,32859.022222,-21572.266667,-32859.022222,11741.866667,51791.644444,-4733.155555,-60256.711111,9739.377777,63351.466667,-3640.888889,-59255.466666,-8100.977778,69358.933333,-2002.488889,-48332.8,-2002.488889,35043.555556,3185.777778,-70360.177778,9193.244444,5279.288889,-4096,66810.311111,-5097.244444,-66628.266667,3185.777778,45875.2,9648.355556,-40868.977778,14825699.555555,12704699.733334,22629580.8,272065.422222,-195151.644445,7463.822223,-626688,769865.955555,-818380.8,1280773.688889,-2777816.177778,3091569.777778,-2703724.088889,2565643.377778,-3210899.911111,2209564.444444,757213.866667,-2785371.022222,2498833.066666,-1760005.688888,2466338.133333,-3384297.244445,4235992.177778,-318213.688889,-383931.733333,-784520.533333,-60802.844445,2266271.288889,-749294.933333,1175460.977778,-3567433.955556,2472618.666667
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M6] rank=6 service=recommendationservice metric=istio-latency-50 baseline=0.007444 peak=0.038828 signed_z=573.944 onset_bin=32 onset_rel_s=731.25 persistence_bins=32
values_compact=raw:[0.007544,0.007475,0.007462,0.007415,0.007448,0.007448,0.007474,0.007492,0.007442,0.007392,0.007369,0.007445,0.007407,0.007451,0.00751,0.007418,0.007358,0.007363,0.007494,0.00752,0.007446,0.007462,0.007475,0.007423,0.007367,0.007367,0.007425,0.007394,0.007361,0.007522,0.00752,0.007513,0.007789,0.009934,0.033378,0.035541,0.033307,0.035316,0.036721,0.034803,0.034766,0.035781,0.035907,0.035827,0.033442,0.035113,0.035345,0.036038,0.036958,0.036273,0.0375,0.036121,0.03687,0.03747,0.036985,0.036582,0.037684,0.038787,0.038167,0.037767,0.037142,0.037637,0.037448,0.037296]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M7] rank=7 service=recommendationservice metric=container-memory-cache baseline=77824.0 peak=422420480.0 signed_z=244.852 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=delta:77824,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,411959296,372736,9994240,-10735616,913408,-827392,880640,-811008,9043968,-9785344,4292608,-3018752,8486912,-9314304,425984,-146239488,147394560,-1556480,8372224,-79593472,-105676800,179965952,-2646016,-113192960,118042624,-3039232,-80789504,83546112,-2654208,3309568,-2064384
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M8] rank=8 service=recommendationservice metric=container-cpu-system-seconds-total baseline=0.401425 peak=12.239033 signed_z=235.189 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=delta:0.394365,0.020683,-0.004722,0.055511,-0.057644,-0.034396,0.050177,-0.013266,-0.018094,0.01792,-0.019224,-0.016596,0.003723,0.004303,-0.002915,-0.014042,0.050609,0.01675,-0.00549,0.016236,-0.032478,-0.024288,0.013861,-0.002541,-0.005537,0.041133,0.06956,-0.098327,0.04451,-0.133327,0.104271,-0.009013,-0.010834,6.618445,3.334003,1.216552,-0.190564,-2.006863,1.701587,0.492479,0.065516,-0.053659,-0.04903,0.038329,0.592427,-0.455478,-0.398406,0.243448,0.382934,-0.680571,0,0.508389,-0.19311,0.210502,-0.35257,0.182473,0.511949,-0.635373,-0.152063,0.743094,-0.035847,-0.32497,0.295285,-0.097175
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M9] rank=9 service=recommendationservice metric=container-memory-working-set-bytes baseline=44238313.244444 peak=62779392.0 signed_z=217.774 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=delta:44105728,28672,0,8192,-20480,45056,4096,4096,24576,-24576,28672,20480,0,20480,-4096,8192,8192,-8192,8192,4096,139264,-159744,32768,63488,75776,-299008,180224,-40960,94208,16384,0,32768,-12288,17526784,-368640,-9805824,10686464,-974848,1081344,-1036288,864256,-8888320,9310208,-4014080,2908160,-8372224,9428992,-770048,-10735616,9666560,1777664,-8470528,5181440,-2945024,3006464,2527232,-9818112,5257216,1124352,-1601536,753664,2453504,-3219456,1896448
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M10] rank=10 service=gke-gke-cluster-default-pool-2e1807ce-w819 metric=node-disk-writes-completed-total baseline=81.090278 peak=312.466667 signed_z=215.687 onset_bin=32 onset_rel_s=731.25 persistence_bins=32
values_compact=delta:80.466667,-0.044445,0.222222,-1.022222,0.8,1,-0.888889,-0.8,2.4,0,0.577778,0.666667,-0.666667,0.4,-1.133333,-0.533334,-0.955555,1.044444,-0.4,-1.644444,0.8,-0.466667,0.844445,0.533333,-0.222222,1.244444,-0.555555,-1.577778,0.2,0.044444,0.111111,0.222223,57.511111,53.466666,96.911112,2,1.177777,-1.133333,0.088889,1.911111,-3.822222,6.577778,-10.111112,14.244445,-13.044445,10.688889,-13.644444,10.866667,5.088888,-13.022222,11.866667,-6.444445,6.866667,-12.755555,18.777777,-4.8,2.533334,-0.244445,1.111111,9.133334,-6,4.444444,-12.6,10.088889
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M11] rank=11 service=emailservice metric=istio-latency-95 baseline=0.004811 peak=0.01075 signed_z=200.655 onset_bin=52 onset_rel_s=1181.25 persistence_bins=4
values_compact=rle:0.0048*1,0.004886*1,0.004879*1,0.0048*7,0.004884*1,0.00489*1,0.0048*39,0.004884*1,0.00675*1,0.00575*1,0.0048*8,0.007417*1,0.007833*1
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M12] rank=12 service=recommendationservice metric=istio-latency-99 baseline=0.019106 peak=0.817045 signed_z=178.368 onset_bin=32 onset_rel_s=731.25 persistence_bins=32
values_compact=raw:[0.025719,0.021858,0.02122,0.018795,0.021479,0.019494,0.021003,0.021083,0.019737,0.018589,0.011333,0.020338,0.020362,0.021601,0.022737,0.020935,0.01445,0.011355,0.021238,0.02289,0.023752,0.023966,0.021303,0.015525,0.009982,0.009992,0.013423,0.011583,0.017594,0.022741,0.02245,0.022873,0.185235,0.2378,0.536667,0.769722,0.544444,0.242448,0.242936,0.24216,0.241285,0.241403,0.241886,0.242168,0.241179,0.24491,0.244,0.297375,0.29125,0.244103,0.813636,0.804773,0.244656,0.244833,0.408182,0.416377,0.2965,0.249769,0.245192,0.244068,0.246124,0.245214,0.239769,0.241669]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[709.0,1440.0]

=== LOG SUMMARY ===
{"entries":[{"change_pct":-33.3,"n_during":10,"n_pre":15,"service":"redis"},{"change_pct":2.3,"n_during":6585,"n_pre":6440,"service":"recommendationservice"},{"change_pct":2.2,"n_during":5255,"n_pre":5143,"service":"adservice"},{"change_pct":1.2,"n_during":8907,"n_pre":8803,"service":"cartservice"},{"change_pct":1.0,"n_during":951,"n_pre":942,"service":"checkoutservice"},{"change_pct":1.0,"n_during":317,"n_pre":314,"service":"emailservice"},{"change_pct":1.0,"n_during":634,"n_pre":628,"service":"paymentservice"},{"change_pct":-0.4,"n_during":26971,"n_pre":27091,"service":"currencyservice"}],"mode":"volume","omitted_services":2,"service_count":10}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":1900.1,"error_pct":0.0,"p95_during_ms":99.33895,"p95_pre_ms":4.966699999999997,"service":"recommendationservice","spans":26626},{"delta_pct":20.7,"error_pct":0.0,"p95_during_ms":0.45459999999999745,"p95_pre_ms":0.3766999999999999,"service":"paymentservice","spans":919},{"delta_pct":11.0,"error_pct":0.0,"p95_during_ms":216.54259999999965,"p95_pre_ms":195.01069999999999,"service":"frontend","spans":199476},{"delta_pct":5.1,"error_pct":0.0,"p95_during_ms":0.44460000000000005,"p95_pre_ms":0.42289999999999983,"service":"emailservice","spans":1207},{"delta_pct":4.2,"error_pct":0.0,"p95_during_ms":0.025,"p95_pre_ms":0.024,"service":"productcatalogservice","spans":99915},{"delta_pct":1.7,"error_pct":0.0,"p95_during_ms":0.183,"p95_pre_ms":0.18,"service":"currencyservice","spans":54344},{"delta_pct":0.4,"error_pct":0.0,"p95_during_ms":211.93350000000004,"p95_pre_ms":211.02920000000003,"service":"checkoutservice","spans":8690}],"omitted_services":0,"service_count":7}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=3 omitted_edges=0
[{"evidence_source":"trace","onset_rel_s":735.0,"rank":1,"service":"recommendationservice","severity_z":200.999},{"evidence_source":"metric","onset_rel_s":879.0,"rank":2,"service":"gke-gke-cluster-default-pool-2e1807ce-xte3","severity_z":17.045},{"evidence_source":"metric","onset_rel_s":1090.2,"rank":3,"service":"gke-gke-cluster-default-pool-2e1807ce-w819","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1189.8,"rank":4,"service":"paymentservice","severity_z":30.562},{"evidence_source":"metric","onset_rel_s":1203.0,"rank":5,"service":"adservice","severity_z":21.897},{"evidence_source":"trace","onset_rel_s":1215.0,"rank":6,"service":"emailservice","severity_z":8.116},{"evidence_source":"metric","onset_rel_s":1396.2,"rank":7,"service":"checkoutservice","severity_z":11.399},{"evidence_source":"trace","onset_rel_s":1425.0,"rank":8,"service":"frontend","severity_z":4.514},{"evidence_source":"none","onset_rel_s":null,"rank":9,"service":"frontend-external","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":10,"service":"gke-gke-cluster-default-pool-2e1807ce-cx8g","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":11,"service":"productcatalogservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":12,"service":"loadgenerator","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":13,"service":"currencyservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":14,"service":"cartservice","severity_z":0.0}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"currencyservice","caller":"checkoutservice"},{"callee":"emailservice","caller":"checkoutservice"},{"callee":"paymentservice","caller":"checkoutservice"},{"callee":"productcatalogservice","caller":"checkoutservice"},{"callee":"checkoutservice","caller":"frontend"},{"callee":"currencyservice","caller":"frontend"},{"callee":"productcatalogservice","caller":"frontend"},{"callee":"recommendationservice","caller":"frontend"},{"callee":"productcatalogservice","caller":"recommendationservice"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

{"confidence":"high","reason":"Rank recommendationservice first because recommendationservice has direct container-memory-mapped-file evidence (signed-z 999, persistence 31 bins); although frontend is salient, the caller path frontend -> recommendationservice means a disturbance in the callee can propagate back toward that caller-side symptom.","services":["recommendationservice","frontend"]}

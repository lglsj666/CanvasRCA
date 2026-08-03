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
opaque_id: INC-17070012353F
observation_window={"duration_rel_s":1440.0,"source_metric_rows":1441}
selection_summary={"candidate_count":17,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":260,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["adservice","cartservice","checkoutservice","currencyservice","emailservice","frontend","frontend-external","gke-gke-cluster-default-pool-2e1807ce-0e4z","gke-gke-cluster-default-pool-2e1807ce-cx8g","gke-gke-cluster-default-pool-2e1807ce-w819","gke-gke-cluster-default-pool-2e1807ce-xte3","loadgenerator","paymentservice","productcatalogservice","recommendationservice","redis","shippingservice"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[11.25,33.75,56.25,78.75,101.25,123.75,146.25,168.75,191.25,213.75,236.25,258.75,281.25,303.75,326.25,348.75,371.25,393.75,416.25,438.75,461.25,483.75,506.25,528.75,551.25,573.75,596.25,618.75,641.25,663.75,686.25,708.75,731.25,753.75,776.25,798.75,821.25,843.75,866.25,888.75,911.25,933.75,956.25,978.75,1001.25,1023.75,1046.25,1068.75,1091.25,1113.75,1136.25,1158.75,1181.25,1203.75,1226.25,1248.75,1271.25,1293.75,1316.25,1338.75,1361.25,1383.75,1406.25,1428.75]
[M1] rank=1 service=recommendationservice metric=istio-latency-50 baseline=0.007405 peak=0.261283 signed_z=999.0 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=raw:[0.007474,0.00742,0.00744,0.007407,0.007369,0.007419,0.007442,0.007461,0.007431,0.007433,0.007465,0.007426,0.007373,0.007331,0.007331,0.007354,0.007344,0.007368,0.00741,0.007396,0.00738,0.0074,0.007408,0.007442,0.00752,0.007469,0.007386,0.007416,0.007428,0.007378,0.007348,0.007308,0.007429,0.079858,0.239119,0.251157,0.251279,0.254892,0.2575,0.248511,0.247794,0.252403,0.251603,0.250065,0.249225,0.249248,0.252513,0.25016,0.250643,0.251348,0.25,0.249055,0.249433,0.253079,0.251269,0.249942,0.249812,0.251739,0.250895,0.249457,0.251636,0.249817,0.248533,0.250954]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M2] rank=2 service=recommendationservice metric=istio-latency-90 baseline=0.00956 peak=0.454512 signed_z=999.0 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=delta:0.009608,-0.000015,0.000059,-0.000054,-0.000047,0.000018,0.000025,0.00003,-0.000053,0.000004,0.00004,-0.000056,-0.000041,-0.00003,0,0.000019,0.000018,0,0,-0.000012,-0.000011,0.000042,0.000022,0.00005,0.00012,-0.000102,-0.000142,0.000022,0.000003,-0.00002,0.000049,0.000003,0.000163,0.408793,0.032467,-0.000761,0.000045,0.003248,0.000496,-0.004506,-0.000252,0.001239,-0.00016,-0.000321,-0.000261,0.000008,0.001761,-0.00052,-0.000859,0.000474,0.000431,-0.000874,-0.00035,0.000806,-0.000362,-0.000317,0,0.001417,-0.00022,-0.001316,0.000509,-0.000388,-0.000438,0.00069
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M3] rank=3 service=productcatalogservice metric=istio-latency-95 baseline=0.0047 peak=0.142681 signed_z=999.0 onset_bin=32 onset_rel_s=731.25 persistence_bins=32
values_compact=raw:[0.004755,0.004721,0.004713,0.004687,0.00468,0.004691,0.004704,0.0047,0.004687,0.004685,0.004684,0.004693,0.004699,0.004696,0.004696,0.004706,0.004705,0.004697,0.004695,0.004689,0.004689,0.004706,0.004706,0.004683,0.004735,0.004743,0.004696,0.004689,0.004686,0.004692,0.004697,0.004696,0.004782,0.004938,0.134987,0.135565,0.133605,0.133779,0.133209,0.138468,0.136893,0.133528,0.135124,0.13545,0.135659,0.136665,0.135235,0.132971,0.134741,0.1337,0.133703,0.136291,0.13505,0.133209,0.135308,0.135326,0.135424,0.13475,0.135437,0.13732,0.134397,0.136092,0.138112,0.135942]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M4] rank=4 service=recommendationservice metric=istio-latency-95 baseline=0.009849 peak=0.479451 signed_z=999.0 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=raw:[0.009875,0.009864,0.009929,0.009872,0.009823,0.009838,0.009863,0.009894,0.009837,0.009843,0.009883,0.009825,0.009787,0.009757,0.009757,0.009777,0.009796,0.009795,0.00979,0.009778,0.009767,0.009811,0.009836,0.009888,0.010732,0.009904,0.009756,0.009776,0.009778,0.009763,0.00982,0.009829,0.009997,0.463258,0.477917,0.475106,0.475128,0.47833,0.478562,0.474747,0.474621,0.47524,0.47516,0.475,0.474869,0.474873,0.476382,0.476111,0.475064,0.475637,0.476163,0.4754,0.474905,0.475308,0.475127,0.474969,0.474969,0.476306,0.476163,0.474909,0.475164,0.474969,0.474751,0.475095]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M5] rank=5 service=productcatalogservice metric=istio-latency-99 baseline=0.00497 peak=0.228701 signed_z=999.0 onset_bin=32 onset_rel_s=731.25 persistence_bins=32
values_compact=raw:[0.004992,0.004973,0.004969,0.004948,0.004943,0.004956,0.004966,0.004958,0.004948,0.004947,0.004948,0.004958,0.004959,0.004954,0.004953,0.004956,0.004955,0.004949,0.004947,0.004948,0.004948,0.004966,0.004968,0.00495,0.004998,0.005028,0.004952,0.004947,0.004944,0.004946,0.004948,0.004948,0.008215,0.195793,0.228544,0.228009,0.226721,0.227119,0.22726,0.227744,0.227379,0.226706,0.227025,0.22709,0.227132,0.227333,0.227047,0.226594,0.226968,0.227275,0.227043,0.227259,0.22701,0.226642,0.227062,0.227065,0.227085,0.22695,0.227087,0.227464,0.226879,0.227218,0.228198,0.227804]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M6] rank=6 service=gke-gke-cluster-default-pool-2e1807ce-xte3 metric=node-memory-active-bytes baseline=5690.153086 peak=28685653.333333 signed_z=999.0 onset_bin=42 onset_rel_s=956.25 persistence_bins=2
values_compact=delta:6098.488889,-273.066667,-182.044444,-273.066667,2275.555556,-637.155556,-1820.444444,-910.222223,91.022223,2730.666666,0,-637.155555,-1092.266667,91.022222,-91.022222,-2093.511111,728.177778,2639.644444,1092.266667,-1456.355556,-1820.444444,637.155555,1547.377778,-1274.311111,-273.066667,1274.311112,273.066666,-910.222222,-2093.511111,1001.244444,1820.444445,-546.133334,-910.222222,1183.288889,-546.133333,-1092.266667,-819.2,91.022222,3913.955556,-1274.311111,-2912.711111,182.044444,28680283.022222,1638.4,-28679554.844444,-1456.355556,-1365.333333,728.177778,1183.288889,637.155555,1183.288889,910.222222,-910.222222,-1274.311111,-728.177778,-455.111111,-273.066667,1638.4,637.155556,-1638.4,-1547.377778,182.044445,910.222222,637.155555
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M7] rank=7 service=gke-gke-cluster-default-pool-2e1807ce-0e4z metric=node-disk-reads-completed-total baseline=0.0 peak=0.088889 signed_z=999.0 onset_bin=32 onset_rel_s=731.25 persistence_bins=4
values_compact=rle:0*32,0.066667*2,0*17,0.088889*2,0*11
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M8] rank=8 service=gke-gke-cluster-default-pool-2e1807ce-0e4z metric=node-disk-read-bytes-total baseline=0.0 peak=8647.111111 signed_z=999.0 onset_bin=32 onset_rel_s=731.25 persistence_bins=4
values_compact=rle:0*32,910.222222*2,0*17,8647.111111*2,0*11
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M9] rank=9 service=frontend metric=istio-latency-50 baseline=0.046597 peak=0.35402 signed_z=150.01 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=raw:[0.056122,0.048557,0.046549,0.046957,0.046522,0.04561,0.046313,0.047884,0.04821,0.046515,0.04545,0.045472,0.04505,0.045968,0.046621,0.04731,0.04697,0.047876,0.048156,0.046264,0.04639,0.046604,0.044762,0.043135,0.04556,0.046488,0.044321,0.044523,0.044551,0.04625,0.046604,0.045278,0.046591,0.23,0.334917,0.34542,0.340023,0.336659,0.338349,0.345247,0.347136,0.34033,0.340504,0.338396,0.334928,0.33982,0.342244,0.347724,0.346445,0.334736,0.33657,0.34345,0.3438,0.347738,0.340267,0.333711,0.33828,0.337592,0.339924,0.345706,0.346825,0.348057,0.352794,0.342572]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M10] rank=10 service=adservice metric=container-memory-failures-total baseline=5.137493 peak=425.148711 signed_z=112.592 onset_bin=46 onset_rel_s=1046.25 persistence_bins=2
values_compact=raw:[3.860929,3.355193,3.448706,5.862174,3.073049,2.107192,4.554771,4.328974,5.029022,5.740018,2.394428,1.996207,3.777681,2.021904,0.665544,6.350223,16.584584,15.461034,8.453165,7.437846,7.522396,3.610783,2.136509,2.872274,10.720642,11.306621,4.582784,2.838688,3.864052,3.968873,2.247655,3.881432,4.540336,5.878867,4.212608,4.679275,3.010726,0.396452,3.75,5.191486,2.524497,4.205232,0.466853,6.706204,6.993506,0.580097,372.147227,298.446034,4.107089,1.574919,6.624244,6.944598,2.80041,4.673937,5.444727,5.948513,4.661532,0.413608,2.106725,3.750497,3.127699,1.631765,3.115539,4.330762]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M11] rank=11 service=recommendationservice metric=istio-latency-99 baseline=0.015328 peak=0.499472 signed_z=106.616 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=raw:[0.019334,0.01891,0.020959,0.019186,0.020283,0.020109,0.0201,0.02,0.017288,0.017542,0.0197,0.016086,0.010281,0.009972,0.009971,0.009993,0.01288,0.012511,0.01035,0.00999,0.009978,0.014732,0.017733,0.020212,0.022718,0.019799,0.009966,0.009986,0.009987,0.009978,0.01631,0.017312,0.022596,0.499061,0.499407,0.495021,0.495026,0.498186,0.498195,0.494949,0.494924,0.495048,0.495032,0.495,0.494974,0.494975,0.496281,0.49621,0.495013,0.495664,0.496266,0.495592,0.494981,0.495062,0.495025,0.494994,0.494994,0.496268,0.496187,0.494982,0.495033,0.494994,0.49495,0.495019]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M12] rank=12 service=checkoutservice metric=istio-latency-95 baseline=0.230889 peak=0.78125 signed_z=44.66 onset_bin=33 onset_rel_s=753.75 persistence_bins=2
values_compact=raw:[0.248594,0.249135,0.237386,0.237647,0.236458,0.228929,0.227895,0.228529,0.218333,0.218958,0.22,0.22,0.233676,0.232868,0.231029,0.253125,0.248026,0.234674,0.234625,0.229375,0.232614,0.24425,0.245,0.222404,0.21875,0.216386,0.215,0.20875,0.228036,0.234211,0.2315,0.229536,0.229107,0.6625,0.75,0.240639,0.235417,0.236974,0.233393,0.234732,0.2375,0.232195,0.231912,0.233026,0.226,0.225625,0.2305,0.234311,0.22675,0.20875,0.229844,0.228396,0.225156,0.227882,0.229265,0.234375,0.23625,0.232891,0.224286,0.210167,0.210833,0.221964,0.228,0.229808]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[710.0,1440.0]

=== LOG SUMMARY ===
{"entries":[{"change_pct":-33.3,"n_during":10,"n_pre":15,"service":"redis"},{"change_pct":-10.0,"n_during":948,"n_pre":1053,"service":"checkoutservice"},{"change_pct":-10.0,"n_during":316,"n_pre":351,"service":"emailservice"},{"change_pct":-10.0,"n_during":632,"n_pre":702,"service":"paymentservice"},{"change_pct":-4.9,"n_during":30311,"n_pre":31889,"service":"frontend"},{"change_pct":-4.9,"n_during":5142,"n_pre":5406,"service":"shippingservice"},{"change_pct":-4.7,"n_during":5102,"n_pre":5352,"service":"adservice"},{"change_pct":-4.3,"n_during":8804,"n_pre":9203,"service":"cartservice"}],"mode":"volume","omitted_services":2,"service_count":10}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":4233.6,"error_pct":0.0,"p95_during_ms":204.94404999999998,"p95_pre_ms":4.729199999999997,"service":"recommendationservice","spans":26760},{"delta_pct":671.0,"error_pct":0.0,"p95_during_ms":439.298,"p95_pre_ms":56.978249999999996,"service":"frontend","spans":201967},{"delta_pct":8.3,"error_pct":0.0,"p95_during_ms":0.026,"p95_pre_ms":0.024,"service":"productcatalogservice","spans":100471},{"delta_pct":-5.9,"error_pct":0.0,"p95_during_ms":0.4175999999999999,"p95_pre_ms":0.44379999999999964,"service":"paymentservice","spans":955},{"delta_pct":-5.2,"error_pct":0.0,"p95_during_ms":0.43529999999999996,"p95_pre_ms":0.4593,"service":"emailservice","spans":1243},{"delta_pct":-1.7,"error_pct":0.0,"p95_during_ms":70.01529999999998,"p95_pre_ms":71.209,"service":"checkoutservice","spans":9084},{"delta_pct":0.5,"error_pct":0.0,"p95_during_ms":0.214,"p95_pre_ms":0.213,"service":"currencyservice","spans":55720}],"omitted_services":0,"service_count":7}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=3 omitted_edges=1
[{"evidence_source":"metric","onset_rel_s":721.8,"rank":1,"service":"gke-gke-cluster-default-pool-2e1807ce-0e4z","severity_z":999.0},{"evidence_source":"trace","onset_rel_s":735.0,"rank":2,"service":"recommendationservice","severity_z":420.724},{"evidence_source":"trace","onset_rel_s":735.0,"rank":3,"service":"frontend","severity_z":66.79},{"evidence_source":"metric","onset_rel_s":748.8,"rank":4,"service":"checkoutservice","severity_z":44.66},{"evidence_source":"metric","onset_rel_s":750.0,"rank":5,"service":"cartservice","severity_z":11.343},{"evidence_source":"metric","onset_rel_s":769.2,"rank":6,"service":"productcatalogservice","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":955.2,"rank":7,"service":"gke-gke-cluster-default-pool-2e1807ce-xte3","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1036.2,"rank":8,"service":"adservice","severity_z":112.592},{"evidence_source":"none","onset_rel_s":null,"rank":9,"service":"paymentservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":10,"service":"gke-gke-cluster-default-pool-2e1807ce-w819","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":11,"service":"gke-gke-cluster-default-pool-2e1807ce-cx8g","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":12,"service":"emailservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":13,"service":"currencyservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":14,"service":"shippingservice","severity_z":0.0}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"currencyservice","caller":"checkoutservice"},{"callee":"emailservice","caller":"checkoutservice"},{"callee":"paymentservice","caller":"checkoutservice"},{"callee":"productcatalogservice","caller":"checkoutservice"},{"callee":"checkoutservice","caller":"frontend"},{"callee":"currencyservice","caller":"frontend"},{"callee":"productcatalogservice","caller":"frontend"},{"callee":"recommendationservice","caller":"frontend"},{"callee":"productcatalogservice","caller":"recommendationservice"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

{"confidence":"high","reason":"Rank recommendationservice first because recommendationservice has direct istio-latency-50 evidence (signed-z 999, persistence 31 bins); although frontend is salient, the caller path frontend -> recommendationservice means a disturbance in the callee can propagate back toward that caller-side symptom.","services":["recommendationservice","frontend"]}

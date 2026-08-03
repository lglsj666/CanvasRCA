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
opaque_id: INC-E86EBFCACB90
observation_window={"duration_rel_s":1440.0,"source_metric_rows":1441}
selection_summary={"candidate_count":17,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":269,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["adservice","cartservice","checkoutservice","currencyservice","emailservice","frontend","frontend-external","gke-gke-cluster-default-pool-2e1807ce-0e4z","gke-gke-cluster-default-pool-2e1807ce-cx8g","gke-gke-cluster-default-pool-2e1807ce-w819","gke-gke-cluster-default-pool-2e1807ce-xte3","loadgenerator","paymentservice","productcatalogservice","recommendationservice","redis","shippingservice"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[11.25,33.75,56.25,78.75,101.25,123.75,146.25,168.75,191.25,213.75,236.25,258.75,281.25,303.75,326.25,348.75,371.25,393.75,416.25,438.75,461.25,483.75,506.25,528.75,551.25,573.75,596.25,618.75,641.25,663.75,686.25,708.75,731.25,753.75,776.25,798.75,821.25,843.75,866.25,888.75,911.25,933.75,956.25,978.75,1001.25,1023.75,1046.25,1068.75,1091.25,1113.75,1136.25,1158.75,1181.25,1203.75,1226.25,1248.75,1271.25,1293.75,1316.25,1338.75,1361.25,1383.75,1406.25,1428.75]
[M1] rank=1 service=productcatalogservice metric=container-memory-failures-total baseline=47.103602 peak=21838.400216 signed_z=999.0 onset_bin=32 onset_rel_s=731.25 persistence_bins=32
values_compact=delta:46.474454,-7.298438,-10.55664,2.610008,18.224988,6.673682,-1.603167,-1.483547,-9.733068,5.590535,12.203415,10.395978,-7.722923,4.114084,-20.355023,-9.943048,9.394463,-1.594276,0.709778,-1.525027,21.354127,-11.252666,-37.014356,-1.247669,37.148524,-10.856194,1.243369,-1.521192,3.604881,5.035509,-11.179004,-3.839702,4684.021061,8579.624495,6460.557598,1002.997338,-375.377341,-1267.841041,1746.475807,432.757814,-878.830109,209.720062,-68.865939,51.961015,189.319732,-1074.756363,507.144151,455.676182,563.745734,-577.884846,-567.196101,722.640045,-372.512729,-414.987978,130.975832,1040.987056,-3559.976229,2702.086734,-6434.283601,7227.795582,-186.203031,-410.091356,-353.507826,-547.023867
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M2] rank=2 service=productcatalogservice metric=container-memory-mapped-file baseline=0.0 peak=2211840.0 signed_z=999.0 onset_bin=32 onset_rel_s=731.25 persistence_bins=32
values_compact=rle:0*32,2211840*32
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M3] rank=3 service=adservice metric=istio-error-total baseline=0.0 peak=0.133 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=rle:0*34,0.067*1,0*7,0.133*1,0*4,0.067*1,0*1,0.067*1,0*13,0.133*1
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M4] rank=4 service=recommendationservice metric=istio-latency-50 baseline=0.007476 peak=0.084443 signed_z=999.0 onset_bin=32 onset_rel_s=731.25 persistence_bins=32
values_compact=raw:[0.007489,0.007477,0.007491,0.007506,0.007464,0.00742,0.007476,0.007491,0.00747,0.007506,0.0075,0.007483,0.0075,0.007524,0.007518,0.007503,0.007503,0.007488,0.007446,0.007439,0.007469,0.00747,0.007429,0.007436,0.007467,0.007476,0.007476,0.00748,0.00747,0.007464,0.007454,0.007443,0.007642,0.008914,0.077419,0.077326,0.078133,0.076106,0.078629,0.079157,0.08034,0.08175,0.079882,0.079144,0.078028,0.077103,0.080548,0.079087,0.077221,0.079615,0.076028,0.076478,0.084443,0.083795,0.076336,0.07592,0.080471,0.081774,0.079603,0.080349,0.079602,0.081422,0.080919,0.079145]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M5] rank=5 service=cartservice metric=istio-latency-90 baseline=0.004745 peak=0.1925 signed_z=999.0 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=raw:[0.004717,0.004685,0.004758,0.004786,0.004726,0.004693,0.004675,0.004672,0.004702,0.004756,0.004724,0.00468,0.004769,0.004787,0.004757,0.00474,0.004774,0.004802,0.004731,0.004714,0.004709,0.004709,0.004712,0.004769,0.004799,0.004818,0.004833,0.004801,0.00474,0.00474,0.004787,0.004761,0.004756,0.006081,0.00827,0.008356,0.009037,0.008557,0.008904,0.009078,0.00829,0.00827,0.008066,0.008565,0.009163,0.008259,0.009361,0.009799,0.008413,0.008019,0.007684,0.008525,0.075,0.121,0.009497,0.009158,0.009223,0.008942,0.009994,0.009985,0.008256,0.008614,0.008788,0.008249]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M6] rank=6 service=productcatalogservice metric=istio-latency-90 baseline=0.004419 peak=0.738462 signed_z=999.0 onset_bin=32 onset_rel_s=731.25 persistence_bins=32
values_compact=raw:[0.004395,0.004399,0.004404,0.004403,0.004396,0.004409,0.004421,0.004403,0.004394,0.004405,0.004413,0.004412,0.004415,0.004416,0.004411,0.004434,0.004427,0.004413,0.004417,0.004421,0.004426,0.004423,0.004414,0.004422,0.004424,0.004436,0.004461,0.004445,0.00443,0.00444,0.00445,0.00444,0.004512,0.082128,0.211818,0.23693,0.283482,0.346909,0.409615,0.288889,0.211768,0.231688,0.231649,0.255488,0.305342,0.222864,0.505607,0.679813,0.560656,0.468108,0.295175,0.296369,0.504348,0.512081,0.27803,0.385364,0.637054,0.631144,0.564957,0.44984,0.325794,0.319,0.218868,0.248542]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M7] rank=7 service=recommendationservice metric=istio-latency-90 baseline=0.009586 peak=1.738095 signed_z=999.0 onset_bin=32 onset_rel_s=731.25 persistence_bins=32
values_compact=raw:[0.009589,0.009584,0.009579,0.0096,0.009535,0.009515,0.009623,0.009628,0.009542,0.009603,0.009606,0.009555,0.009614,0.009647,0.009622,0.0096,0.009625,0.009606,0.009525,0.009508,0.009543,0.009557,0.009563,0.009616,0.009629,0.00962,0.009678,0.009646,0.009537,0.009536,0.009543,0.00958,0.009918,0.109474,0.829167,0.844737,0.895833,0.5775,1.019048,1.1125,1.238889,1.41,1.22875,1.428333,1.526531,1.223077,1.534375,1.472159,1.162857,1.461413,1.135,1.28875,1.607075,1.659174,1.388043,0.233615,1.315,1.436047,1.361446,1.355618,1.3,1.615566,1.574038,1.162857]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M8] rank=8 service=cartservice metric=istio-latency-95 baseline=0.005105 peak=0.752692 signed_z=999.0 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=raw:[0.004924,0.004889,0.004967,0.004996,0.004933,0.004898,0.00488,0.004875,0.004908,0.004965,0.004931,0.004885,0.004978,0.004997,0.004965,0.004947,0.004984,0.005398,0.004939,0.00492,0.004915,0.004916,0.004919,0.004978,0.005333,0.005905,0.00675,0.00547,0.004947,0.004948,0.004998,0.00497,0.004965,0.008621,0.009429,0.00941,0.010911,0.009693,0.304167,0.328125,0.009401,0.009425,0.009199,0.009863,0.124375,0.009441,0.546277,0.670565,0.009562,0.009156,0.008882,0.00988,0.667969,0.649135,0.32875,0.014686,0.021672,0.009965,0.5485,0.546,0.009346,0.009718,0.009761,0.009204]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M9] rank=9 service=productcatalogservice metric=istio-latency-95 baseline=0.004718 peak=1.645385 signed_z=999.0 onset_bin=32 onset_rel_s=731.25 persistence_bins=32
values_compact=delta:0.004706,0,0.000001,0,-0.000002,0.000007,0.000008,-0.000007,-0.000006,0.000004,0.000002,0,0.000003,0,-0.000005,0.000015,-0.000004,-0.000011,0.000007,0.000001,0,-0.000002,-0.000005,0.000006,0.000001,0.000011,0.00002,-0.000016,-0.000014,0.000007,0.000009,-0.000004,0.000082,0.092081,1.177226,0.108481,0.060206,0.005706,0.013445,-0.035813,-0.065648,0.018935,0.016756,0.054447,-0.022355,-0.056561,0.16668,0.077338,-0.090946,-0.063978,-0.079545,0.057395,0.134592,-0.044507,-0.140848,0.114191,0.104437,-0.027805,-0.046432,-0.101073,-0.050534,0.057147,-0.05766,-0.00094
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M10] rank=10 service=recommendationservice metric=istio-latency-95 baseline=0.00985 peak=2.119048 signed_z=999.0 onset_bin=32 onset_rel_s=731.25 persistence_bins=32
values_compact=raw:[0.009852,0.009848,0.00984,0.009862,0.009793,0.009777,0.009892,0.009895,0.009801,0.009865,0.009869,0.009814,0.009878,0.009913,0.009885,0.009862,0.00989,0.009871,0.009785,0.009767,0.009802,0.009818,0.00983,0.009888,0.0099,0.009888,0.009954,0.009917,0.009796,0.009794,0.009804,0.009847,0.051118,0.538889,1.6475,1.67625,1.721591,1.4965,1.759524,1.80625,1.869444,1.955,1.864375,1.964167,2.013266,1.861538,2.017187,1.98608,1.831429,1.980707,1.8175,1.894375,2.053538,2.079587,1.944022,1.508019,1.9075,1.968023,1.930723,1.927809,1.9,2.057783,2.037019,1.831429]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M11] rank=11 service=productcatalogservice metric=istio-latency-99 baseline=0.004957 peak=2.329077 signed_z=999.0 onset_bin=32 onset_rel_s=731.25 persistence_bins=32
values_compact=raw:[0.004954,0.004952,0.004949,0.004951,0.004953,0.004955,0.004961,0.004961,0.004957,0.004956,0.004953,0.004953,0.004957,0.004957,0.004952,0.00496,0.004958,0.004949,0.004958,0.004958,0.004952,0.004953,0.004951,0.004954,0.004955,0.004965,0.004981,0.004965,0.004952,0.004957,0.004965,0.004966,0.065264,1.763971,2.254824,2.27652,2.288562,2.289703,2.292392,2.285229,2.2721,2.275887,2.279238,2.290127,2.285656,2.274344,2.30768,2.323148,2.304958,2.292163,2.276254,2.287733,2.314651,2.30575,2.27758,2.300418,2.321306,2.315745,2.306458,2.286244,2.276137,2.287566,2.276034,2.275846]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M12] rank=12 service=gke-gke-cluster-default-pool-2e1807ce-w819 metric=node-memory-active-bytes baseline=7174.447407 peak=18990446.153162 signed_z=999.0 onset_bin=42 onset_rel_s=956.25 persistence_bins=21
values_compact=raw:[6826.666667,6735.644444,8556.088889,8829.155556,6735.644444,6007.466667,6644.622222,7554.844444,6735.644444,6462.577778,7554.844444,6553.6,5825.422222,6462.577778,7099.733333,8192.0,7554.844444,6371.555556,6553.6,7099.733333,8100.977778,7736.888889,6189.511111,6280.533333,6826.666667,7008.711111,7463.822222,7099.733333,7372.8,8192.0,8556.088889,8283.022222,8009.955556,7827.911111,7463.822222,7645.866667,7372.8,6917.688889,6644.622222,6553.6,7645.866667,8009.955556,37956.266667,37410.133333,11923.911111,14654.577778,32494.933333,36044.8,19478.755556,25395.2,34133.333333,31948.8,18843420.444444,18838232.177778,43690.666667,41142.044444,74274.133333,103947.377778,80099.555556,70083.996267,106131.911111,18990446.153162,18911323.022222,6462.577778]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[707.0,1440.0]

=== LOG SUMMARY ===
{"entries":[{"error_logs":12,"error_pct":0.02,"service":"frontend","total_logs":55751}],"mode":"errors","omitted_services":9,"service_count":10}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":33965.5,"error_pct":0.0,"p95_during_ms":1675.83335,"p95_pre_ms":4.9194499999999985,"service":"recommendationservice","spans":18730},{"delta_pct":2444.5,"error_pct":0.0,"p95_during_ms":1539.7185,"p95_pre_ms":60.510899999999964,"service":"frontend","spans":140599},{"delta_pct":155.3,"error_pct":0.0,"p95_during_ms":189.70489999999987,"p95_pre_ms":74.30715000000004,"service":"checkoutservice","spans":6212},{"delta_pct":14.7,"error_pct":0.0,"p95_during_ms":0.4795999999999988,"p95_pre_ms":0.4181999999999998,"service":"paymentservice","spans":658},{"delta_pct":10.2,"error_pct":0.0,"p95_during_ms":0.4643,"p95_pre_ms":0.42139999999999983,"service":"emailservice","spans":875},{"delta_pct":3.6,"error_pct":0.0,"p95_during_ms":0.029,"p95_pre_ms":0.028,"service":"productcatalogservice","spans":69646},{"delta_pct":-0.4,"error_pct":0.0,"p95_during_ms":0.223,"p95_pre_ms":0.224,"service":"currencyservice","spans":39383}],"omitted_services":0,"service_count":7}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=3 omitted_edges=2
[{"evidence_source":"trace","onset_rel_s":735.0,"rank":1,"service":"recommendationservice","severity_z":999.0},{"evidence_source":"trace","onset_rel_s":735.0,"rank":2,"service":"frontend","severity_z":339.709},{"evidence_source":"trace","onset_rel_s":735.0,"rank":3,"service":"checkoutservice","severity_z":156.589},{"evidence_source":"metric","onset_rel_s":756.0,"rank":4,"service":"adservice","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":781.2,"rank":5,"service":"shippingservice","severity_z":254.264},{"evidence_source":"metric","onset_rel_s":993.0,"rank":6,"service":"gke-gke-cluster-default-pool-2e1807ce-cx8g","severity_z":999.0},{"evidence_source":"trace","onset_rel_s":1005.0,"rank":7,"service":"productcatalogservice","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1072.2,"rank":8,"service":"cartservice","severity_z":999.0},{"evidence_source":"trace","onset_rel_s":1155.0,"rank":9,"service":"currencyservice","severity_z":7.29},{"evidence_source":"metric","onset_rel_s":1164.0,"rank":10,"service":"gke-gke-cluster-default-pool-2e1807ce-w819","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1279.8,"rank":11,"service":"gke-gke-cluster-default-pool-2e1807ce-xte3","severity_z":685.33},{"evidence_source":"metric","onset_rel_s":1309.2,"rank":12,"service":"emailservice","severity_z":37.776},{"evidence_source":"metric","onset_rel_s":1318.2,"rank":13,"service":"gke-gke-cluster-default-pool-2e1807ce-0e4z","severity_z":999.0},{"evidence_source":"trace","onset_rel_s":1425.0,"rank":14,"service":"paymentservice","severity_z":3.275}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"currencyservice","caller":"checkoutservice"},{"callee":"emailservice","caller":"checkoutservice"},{"callee":"paymentservice","caller":"checkoutservice"},{"callee":"productcatalogservice","caller":"checkoutservice"},{"callee":"checkoutservice","caller":"frontend"},{"callee":"currencyservice","caller":"frontend"},{"callee":"productcatalogservice","caller":"frontend"},{"callee":"recommendationservice","caller":"frontend"},{"callee":"productcatalogservice","caller":"recommendationservice"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

{"confidence":"high","reason":"Rank productcatalogservice first because productcatalogservice has direct container-memory-failures-total evidence (signed-z 999, persistence 32 bins); although recommendationservice is salient, the caller path recommendationservice -> productcatalogservice means a disturbance in the callee can propagate back toward that caller-side symptom.","services":["productcatalogservice","recommendationservice"]}

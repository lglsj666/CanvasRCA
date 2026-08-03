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
opaque_id: INC-62DBD39C2F6B
observation_window={"duration_rel_s":1440.0,"source_metric_rows":1441}
selection_summary={"candidate_count":17,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":266,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["adservice","cartservice","checkoutservice","currencyservice","emailservice","frontend","frontend-external","gke-gke-cluster-default-pool-2e1807ce-0e4z","gke-gke-cluster-default-pool-2e1807ce-cx8g","gke-gke-cluster-default-pool-2e1807ce-w819","gke-gke-cluster-default-pool-2e1807ce-xte3","loadgenerator","paymentservice","productcatalogservice","recommendationservice","redis","shippingservice"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[11.25,33.75,56.25,78.75,101.25,123.75,146.25,168.75,191.25,213.75,236.25,258.75,281.25,303.75,326.25,348.75,371.25,393.75,416.25,438.75,461.25,483.75,506.25,528.75,551.25,573.75,596.25,618.75,641.25,663.75,686.25,708.75,731.25,753.75,776.25,798.75,821.25,843.75,866.25,888.75,911.25,933.75,956.25,978.75,1001.25,1023.75,1046.25,1068.75,1091.25,1113.75,1136.25,1158.75,1181.25,1203.75,1226.25,1248.75,1271.25,1293.75,1316.25,1338.75,1361.25,1383.75,1406.25,1428.75]
[M1] rank=1 service=frontend metric=istio-error-total baseline=0.0 peak=11.133 signed_z=999.0 onset_bin=38 onset_rel_s=866.25 persistence_bins=13
values_compact=rle:0*38,5.533*1,4.467*1,0*2,9.067*1,9.8*1,0*8,5.933*1,6*1,1.867*1,0*1,2.133*1,10.2*1,0*2,8.667*1,9.867*1,11*1,11.133*1
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M2] rank=2 service=frontend-external metric=istio-error-total baseline=0.0 peak=11.267 signed_z=999.0 onset_bin=38 onset_rel_s=866.25 persistence_bins=13
values_compact=rle:0*38,4.133*1,5.867*1,0*2,10.533*1,8.2*1,0*8,7.267*1,4.333*1,3.333*1,0*1,1.4*1,9.333*1,0*2,6.867*1,10.333*1,10.6*1,11.267*1
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M3] rank=3 service=currencyservice metric=istio-latency-50 baseline=0.056557 peak=45.0 signed_z=999.0 onset_bin=33 onset_rel_s=753.75 persistence_bins=30
values_compact=raw:[0.058365,0.057615,0.058244,0.058498,0.056092,0.054554,0.058031,0.059977,0.057122,0.056289,0.057716,0.0578,0.053878,0.053189,0.054778,0.055146,0.055068,0.05364,0.05437,0.057348,0.05983,0.058478,0.056289,0.05621,0.057168,0.057198,0.0586,0.057727,0.053846,0.053871,0.055307,0.05582,0.055719,0.065787,0.229757,0.372059,0.339218,0.277195,0.230635,0.229586,0.362273,0.395225,0.50009,0.653435,0.376276,0.35616,0.380459,0.395,0.493137,0.493137,0.423611,0.368966,0.29878,0.314914,0.450301,0.559932,0.561194,0.553191,0.705,0.525455,0.436475,0.586957,0.386719,null]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000001
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,6,0
[M4] rank=4 service=frontend metric=istio-latency-50 baseline=0.167926 peak=35.4 signed_z=999.0 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=raw:[0.172309,0.184352,0.187351,0.176899,0.164157,0.155567,0.16446,0.171028,0.165909,0.163297,0.176082,0.173513,0.159878,0.163208,0.152941,0.153523,0.165932,0.164241,0.149943,0.157918,0.173292,0.163619,0.160938,0.164264,0.162526,0.171257,0.184672,0.175367,0.172129,0.176642,0.170976,0.174346,0.163121,0.212353,0.994318,1.726923,1.166139,1.032143,0.827068,0.315789,0.625,1.505435,0.007815,0.006636,0.0875,0.841216,1.224138,1.046875,2.834821,2.964876,1.765411,1.192073,0.518456,0.368056,0.00731,0.006765,1.867188,0.28125,0.007708,0.289773,0.988636,0.00646,0.004823,0.004816]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M5] rank=5 service=currencyservice metric=istio-latency-90 baseline=0.09396 peak=57.0 signed_z=999.0 onset_bin=33 onset_rel_s=753.75 persistence_bins=30
values_compact=raw:[0.095107,0.094714,0.095307,0.095415,0.093026,0.092046,0.0954,0.097387,0.096935,0.095122,0.093987,0.093924,0.091854,0.093413,0.09357,0.091694,0.091738,0.091627,0.094641,0.095078,0.093289,0.092656,0.092751,0.09316,0.094138,0.093793,0.095289,0.095219,0.093059,0.0931,0.093514,0.093615,0.094404,0.298695,2.057595,5.983333,1.984122,1.504878,1.466875,0.933969,1.932692,2.136667,1.712015,1.495488,1.10336,1.111176,1.641803,1.588889,35.52,4.011194,2.19127,1.554198,0.964021,0.966043,1.48,3.461864,2.833333,2.575758,6.972222,2.372059,6.430233,12.5,4.864583,null]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000001
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,6,0
[M6] rank=6 service=frontend metric=istio-latency-90 baseline=0.510597 peak=55.08 signed_z=999.0 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=raw:[0.547959,0.664486,0.689209,0.542241,0.478919,0.452647,0.487736,0.553814,0.49139,0.484198,0.539815,0.531739,0.448349,0.468182,0.478426,0.45119,0.474231,0.470984,0.483906,0.534545,0.498794,0.488806,0.480026,0.475739,0.465686,0.460515,0.585377,0.588095,0.507843,0.544231,0.497525,0.497236,0.499459,2.55814,6.267442,19.357143,16.469388,4.394643,4.37234,2.95,5.013158,6.686275,4.067416,2.361765,3.47043,4.520161,4.792308,3.53125,49.17,42.93,7.463115,5.623377,3.76306,3.806641,3.405172,4.046875,8.397727,10.844444,10.955556,8.107955,16.704545,12.883721,0.009399,0.009492]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M7] rank=7 service=recommendationservice metric=istio-latency-90 baseline=0.009608 peak=0.186087 signed_z=999.0 onset_bin=33 onset_rel_s=753.75 persistence_bins=30
values_compact=raw:[0.00969,0.009642,0.0096,0.009528,0.009513,0.009523,0.009538,0.009621,0.009721,0.009664,0.009576,0.009598,0.009602,0.009563,0.009516,0.009516,0.009559,0.009608,0.009585,0.009548,0.009583,0.0096,0.009604,0.009614,0.009557,0.009538,0.009703,0.009713,0.009791,0.009865,0.009566,0.009618,0.009662,0.020911,0.059773,0.132,0.053636,0.056714,0.024787,0.022231,0.023349,0.024427,0.070455,0.0875,0.021428,0.020118,0.019761,0.021763,0.070227,0.060758,0.024944,0.023174,0.024947,0.0315,0.065,0.024555,0.023991,0.023893,0.056667,0.127083,0.178559,0.176364,0.0175,null]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000001
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,6,0
[M8] rank=8 service=currencyservice metric=istio-latency-95 baseline=0.103001 peak=58.5 signed_z=999.0 onset_bin=33 onset_rel_s=753.75 persistence_bins=30
values_compact=raw:[0.0997,0.099351,0.099906,0.10101,0.097643,0.096732,0.102484,0.148079,0.143092,0.099981,0.098535,0.098434,0.096585,0.098441,0.09842,0.096268,0.096326,0.096385,0.099683,0.099781,0.097471,0.096913,0.097286,0.097783,0.098776,0.098361,0.099888,0.099914,0.097961,0.098003,0.09829,0.098346,0.09924,0.820791,3.908333,15.081633,3.5625,2.2066,2.470937,1.7605,3.556034,4.244565,3.564941,2.031508,2.00379,2.14375,2.279615,2.044444,47.76,36.75,3.186012,2.284733,2.185714,2.483065,2.719697,4.419492,4.5,7.037037,11.925926,6.259259,10.40625,21.25,7.09375,null]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000001
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,6,0
[M9] rank=9 service=currencyservice metric=istio-latency-99 baseline=0.214603 peak=59.7 signed_z=999.0 onset_bin=26 onset_rel_s=596.25 persistence_bins=32
values_compact=raw:[0.219435,0.228989,0.236026,0.225816,0.198033,0.170708,0.233997,0.23547,0.232829,0.228991,0.2095,0.207862,0.169051,0.220851,0.213779,0.099919,0.099994,0.131597,0.221223,0.221538,0.206529,0.175499,0.184808,0.20956,0.232809,0.217565,0.384542,0.39081,0.208828,0.216574,0.223397,0.219031,0.224684,2.440797,8.322414,27.016327,25.636735,4.140441,4.849432,4.89,8.33,8.6525,8.226667,2.452084,3.885973,4.235811,4.235811,2.408889,57.552,55.35,4.661012,4.331818,4.384211,4.49593,4.543939,7.2875,8.571429,23.62963,26.385185,9.251852,26.08125,28.25,9.41875,null]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000001
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,6,0
[M10] rank=10 service=productcatalogservice metric=istio-latency-99 baseline=0.004948 peak=0.054222 signed_z=999.0 onset_bin=33 onset_rel_s=753.75 persistence_bins=29
values_compact=delta:0.004974,-0.000004,-0.000024,0.000001,-0.000005,-0.000002,0.000003,0.000005,0.000022,-0.000001,-0.000023,-0.000003,0.000004,0,-0.000001,-0.000003,0.000001,0.000001,-0.000002,-0.000002,0.000001,0,0,0,0.000007,0.000003,-0.000008,-0.000005,0.000007,0.000006,-0.000007,-0.000006,0,0.002879,0.001291,-0.000585,-0.000701,0.000495,-0.001261,-0.000475,0.002416,-0.000036,-0.000831,-0.003094,0.004875,-0.000053,-0.000995,0.00036,0.00042,0.00019,0.007537,0.005579,-0.01155,-0.002109,-0.000407,0.014016,0.013954,-0.027157,0.000114,0.000063,0.011136,0.013019,-0.02907,-0.000007
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M11] rank=11 service=cartservice metric=istio-bytes-90 baseline=0.247269 peak=1.305769 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=raw:[0.247248,0.24721,0.247248,0.2472,0.247405,0.247223,0.247227,0.247273,0.247364,0.247115,0.247261,0.247523,0.247238,0.247092,0.247197,0.247348,0.247395,0.247482,0.247121,0.246994,0.247383,0.247352,0.247201,0.247285,0.247141,0.247285,0.247517,0.247383,0.247212,0.247235,0.2473,0.247285,0.247338,0.247119,0.246687,0.247178,0.247252,0.247273,0.247311,0.247473,0.2477,0.247311,0.246967,0.246336,0.246919,0.247663,0.247581,0.244247,0.247,0.247715,0.247563,0.247219,0.24708,0.246959,0.247243,0.247714,0.247318,0.246877,0.24731,0.246986,0.247169,0.247434,0.247366,0.248065]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M12] rank=12 service=currencyservice metric=istio-bytes-90 baseline=0.244474 peak=0.0975 signed_z=-999.0 onset_bin=32 onset_rel_s=731.25 persistence_bins=31
values_compact=raw:[0.24446,0.244407,0.244409,0.244584,0.244593,0.244463,0.244381,0.244403,0.244507,0.244429,0.24453,0.244432,0.244433,0.244469,0.244489,0.244532,0.24449,0.244399,0.244522,0.24468,0.244407,0.244346,0.244513,0.244486,0.244323,0.244389,0.244536,0.244399,0.244425,0.244548,0.244589,0.244386,0.242122,0.22843,0.098381,0.098304,0.098201,0.098261,0.098409,0.098344,0.098359,0.098413,0.098462,0.098613,0.098607,0.09858,0.098483,0.098235,0.098442,0.098437,0.098485,0.098415,0.098358,0.098466,0.098462,0.098462,0.098439,0.098436,0.098477,0.098453,0.098148,0.097557,0.097557,null]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000001
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,6,0

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[1332.0,1440.0]

=== LOG SUMMARY ===
{"entries":[{"error_logs":2323,"error_pct":4.33,"service":"frontend","total_logs":53608}],"mode":"errors","omitted_services":9,"service_count":10}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":1148.6,"error_pct":0.0,"p95_during_ms":84.81404999999992,"p95_pre_ms":6.792900000000001,"service":"recommendationservice","spans":18872},{"delta_pct":-97.8,"error_pct":0.0,"p95_during_ms":8.8766,"p95_pre_ms":401.421,"service":"checkoutservice","spans":6958},{"delta_pct":-79.5,"error_pct":0.0,"p95_during_ms":0.08379999999999993,"p95_pre_ms":0.408,"service":"emailservice","spans":1036},{"delta_pct":-61.3,"error_pct":0.0,"p95_during_ms":210.24,"p95_pre_ms":543.6973999999991,"service":"frontend","spans":148048},{"delta_pct":-49.6,"error_pct":0.0,"p95_during_ms":0.213,"p95_pre_ms":0.423,"service":"paymentservice","spans":748},{"delta_pct":44.6,"error_pct":0.0,"p95_during_ms":0.03470000000000005,"p95_pre_ms":0.024,"service":"productcatalogservice","spans":72317},{"delta_pct":12.8,"error_pct":0.0,"p95_during_ms":0.26959999999999995,"p95_pre_ms":0.239,"service":"currencyservice","spans":38221}],"omitted_services":0,"service_count":7}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=3 omitted_edges=0
[{"evidence_source":"metric","onset_rel_s":730.2,"rank":1,"service":"gke-gke-cluster-default-pool-2e1807ce-0e4z","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":786.0,"rank":2,"service":"recommendationservice","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":876.0,"rank":3,"service":"frontend-external","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":930.0,"rank":4,"service":"gke-gke-cluster-default-pool-2e1807ce-xte3","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":937.8,"rank":5,"service":"frontend","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":967.2,"rank":6,"service":"paymentservice","severity_z":94.49},{"evidence_source":"metric","onset_rel_s":981.0,"rank":7,"service":"adservice","severity_z":363.82},{"evidence_source":"metric","onset_rel_s":982.8,"rank":8,"service":"productcatalogservice","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1030.8,"rank":9,"service":"checkoutservice","severity_z":153.579},{"evidence_source":"metric","onset_rel_s":1041.0,"rank":10,"service":"cartservice","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1071.0,"rank":11,"service":"currencyservice","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1096.8,"rank":12,"service":"emailservice","severity_z":75.898},{"evidence_source":"metric","onset_rel_s":1351.2,"rank":13,"service":"gke-gke-cluster-default-pool-2e1807ce-w819","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1399.8,"rank":14,"service":"shippingservice","severity_z":427.015}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"currencyservice","caller":"checkoutservice"},{"callee":"emailservice","caller":"checkoutservice"},{"callee":"paymentservice","caller":"checkoutservice"},{"callee":"productcatalogservice","caller":"checkoutservice"},{"callee":"checkoutservice","caller":"frontend"},{"callee":"currencyservice","caller":"frontend"},{"callee":"productcatalogservice","caller":"frontend"},{"callee":"recommendationservice","caller":"frontend"},{"callee":"productcatalogservice","caller":"recommendationservice"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

{"confidence":"high","reason":"Rank currencyservice first because currencyservice has direct istio-latency-50 evidence (signed-z 999, persistence 30 bins); although frontend is salient, the caller path frontend -> currencyservice means a disturbance in the callee can propagate back toward that caller-side symptom.","services":["currencyservice","frontend"]}

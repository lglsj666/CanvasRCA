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
opaque_id: INC-41A0F07B5940
observation_window={"duration_rel_s":1440.0,"source_metric_rows":1441}
selection_summary={"candidate_count":17,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":266,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["adservice","cartservice","checkoutservice","currencyservice","emailservice","frontend","frontend-external","gke-gke-cluster-default-pool-2e1807ce-0e4z","gke-gke-cluster-default-pool-2e1807ce-cx8g","gke-gke-cluster-default-pool-2e1807ce-w819","gke-gke-cluster-default-pool-2e1807ce-xte3","loadgenerator","paymentservice","productcatalogservice","recommendationservice","redis","shippingservice"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[11.25,33.75,56.25,78.75,101.25,123.75,146.25,168.75,191.25,213.75,236.25,258.75,281.25,303.75,326.25,348.75,371.25,393.75,416.25,438.75,461.25,483.75,506.25,528.75,551.25,573.75,596.25,618.75,641.25,663.75,686.25,708.75,731.25,753.75,776.25,798.75,821.25,843.75,866.25,888.75,911.25,933.75,956.25,978.75,1001.25,1023.75,1046.25,1068.75,1091.25,1113.75,1136.25,1158.75,1181.25,1203.75,1226.25,1248.75,1271.25,1293.75,1316.25,1338.75,1361.25,1383.75,1406.25,1428.75]
[M1] rank=1 service=currencyservice metric=istio-latency-50 baseline=0.003256 peak=0.131522 signed_z=999.0 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=raw:[0.003364,0.003238,0.003249,0.003314,0.003229,0.003195,0.003266,0.003219,0.003168,0.003168,0.00318,0.003265,0.00334,0.003229,0.003147,0.003205,0.003357,0.003361,0.003227,0.003345,0.003314,0.003178,0.003248,0.003263,0.003339,0.00339,0.003248,0.003242,0.003272,0.003188,0.003205,0.003252,0.003307,0.003892,0.009989,0.007855,0.008736,0.008265,0.008336,0.008416,0.019492,0.023059,0.077988,0.088437,0.046053,0.064479,0.080594,0.116564,0.083913,0.062888,0.072386,0.07938,0.071598,0.070333,0.084091,0.077029,0.074159,0.02796,0.027118,0.050109,0.072949,0.092979,0.10384,0.020639]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M2] rank=2 service=currencyservice metric=istio-latency-90 baseline=0.005815 peak=1.786207 signed_z=999.0 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=raw:[0.007661,0.005327,0.005634,0.006613,0.00513,0.00495,0.005751,0.004994,0.004902,0.004903,0.004924,0.005755,0.006907,0.005168,0.004864,0.00497,0.007417,0.00738,0.00511,0.007314,0.00689,0.00492,0.005491,0.005747,0.007104,0.007635,0.005533,0.005541,0.006101,0.004938,0.004968,0.005538,0.00644,0.046762,0.465741,0.216004,0.227694,0.227971,0.405988,0.382095,0.481646,0.569118,0.633824,0.597785,0.296579,0.624013,0.804091,1.703448,0.833008,0.574088,0.743073,0.932,0.604545,0.667961,1.352174,0.755155,0.747768,0.403732,0.315019,0.47732,1.048347,1.593269,0.967514,0.524848]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M3] rank=3 service=frontend metric=istio-latency-90 baseline=0.092701 peak=20.98 signed_z=999.0 onset_bin=32 onset_rel_s=731.25 persistence_bins=32
values_compact=raw:[0.091913,0.089035,0.092319,0.095549,0.091389,0.09199,0.092255,0.087888,0.085158,0.085168,0.088598,0.090455,0.09563,0.093452,0.087011,0.089075,0.09879,0.104815,0.093212,0.097245,0.09503,0.089715,0.093312,0.093671,0.097365,0.097147,0.089284,0.093916,0.097455,0.090064,0.089529,0.089921,0.194888,1.516346,2.459859,2.426573,3.757143,2.40137,2.297236,2.725,1.927869,1.873298,4.66129,4.661972,1.931579,1.714286,2.305372,20.98,12.879947,1.9675,2.358216,8.392857,3.083333,2.108163,4.737179,3.87,2.231222,2.368182,2.314035,2.002581,3.151235,4.258929,4.863924,4.279167]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M4] rank=4 service=recommendationservice metric=istio-latency-90 baseline=0.009542 peak=0.146519 signed_z=999.0 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=raw:[0.009614,0.009551,0.009501,0.009534,0.009542,0.009551,0.009553,0.009498,0.0095,0.009516,0.009503,0.009502,0.009515,0.0095,0.009504,0.00953,0.009597,0.009608,0.009537,0.009521,0.009519,0.009521,0.009521,0.00954,0.009564,0.009538,0.009508,0.009628,0.00965,0.009592,0.009576,0.009562,0.00956,0.056098,0.091226,0.099412,0.129348,0.02388,0.020562,0.027778,0.026875,0.021858,0.039318,0.026071,0.02049,0.021435,0.022093,0.074722,0.062825,0.022474,0.024704,0.063095,0.022245,0.038333,0.09,0.024904,0.024016,0.024639,0.028846,0.0375,0.081884,0.083487,0.08087,0.0247]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M5] rank=5 service=currencyservice metric=istio-latency-95 baseline=0.008233 peak=14.84 signed_z=999.0 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=raw:[0.011743,0.007949,0.008585,0.008875,0.00765,0.0072,0.007901,0.007496,0.006795,0.006791,0.006994,0.007968,0.00902,0.008302,0.006349,0.007479,0.009765,0.009624,0.007782,0.009764,0.009501,0.00697,0.007899,0.008062,0.009458,0.009724,0.008092,0.009026,0.008919,0.007117,0.007334,0.007829,0.008617,0.34875,0.905763,0.585417,0.674511,0.611058,0.806539,0.822879,0.8084,0.870956,1.657533,1.495263,0.545833,0.879441,1.102083,14.52,2.320959,0.847263,1.357216,3.304348,0.915289,1.01125,3.232558,1.774457,1.226103,0.944695,0.722324,0.85,1.904339,2.267788,2.42381,0.952973]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M6] rank=6 service=recommendationservice metric=istio-latency-95 baseline=0.0098 peak=0.207753 signed_z=999.0 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=raw:[0.009875,0.009807,0.009753,0.00979,0.0098,0.009809,0.009809,0.009755,0.009756,0.009773,0.00976,0.00976,0.009773,0.009756,0.009761,0.009788,0.009858,0.009872,0.009797,0.009776,0.009775,0.009778,0.009778,0.009798,0.009825,0.009797,0.009763,0.009893,0.009916,0.009854,0.009834,0.009818,0.009817,0.1075,0.16375,0.181102,0.200543,0.106176,0.023669,0.127439,0.112073,0.033889,0.101607,0.096471,0.023838,0.024922,0.027625,0.146562,0.141249,0.056447,0.070163,0.093462,0.08225,0.093636,0.15837,0.090962,0.076125,0.079687,0.066463,0.113462,0.128125,0.116172,0.118429,0.077188]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M7] rank=7 service=currencyservice metric=istio-bytes-99 baseline=2.319975 peak=0.226062 signed_z=-999.0 onset_bin=40 onset_rel_s=911.25 persistence_bins=23
values_compact=raw:[2.319234,2.32037,2.32,2.320024,2.31972,2.319288,2.320053,2.320218,2.319348,2.320536,2.320248,2.319951,2.319801,2.319764,2.32043,2.320383,2.32,2.319484,2.320621,2.320477,2.320548,2.320337,2.320143,2.32,2.320521,2.320298,2.319614,2.318993,2.319468,2.320183,2.321007,2.319875,2.3201,2.3206,2.291001,2.322405,2.307803,2.317582,2.310521,2.320949,0.227848,0.228583,2.182228,2.199083,2.323368,0.228823,0.228742,0.229696,0.229433,0.229184,0.229192,0.228293,0.228132,0.229291,0.229347,0.229221,0.229047,2.269808,2.262236,0.226352,0.226994,0.228955,0.22854,2.325559]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M8] rank=8 service=frontend metric=istio-latency-50 baseline=0.042152 peak=0.920455 signed_z=893.833 onset_bin=32 onset_rel_s=731.25 persistence_bins=32
values_compact=raw:[0.043114,0.041763,0.041244,0.043359,0.04268,0.043156,0.043318,0.041545,0.040298,0.040736,0.042139,0.042137,0.042933,0.042165,0.040798,0.040835,0.042851,0.044477,0.042205,0.042216,0.042078,0.041405,0.042546,0.042122,0.041768,0.041887,0.040718,0.041289,0.042313,0.041494,0.043382,0.043169,0.045896,0.071805,0.487903,0.444969,0.374384,0.371245,0.451687,0.518405,0.42663,0.432471,0.614286,0.671141,0.440789,0.415,0.472074,0.807377,0.445859,0.404589,0.486841,0.449824,0.389563,0.387195,0.481481,0.520942,0.604803,0.543194,0.397196,0.383028,0.621166,0.920455,0.75,0.67638]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M9] rank=9 service=adservice metric=istio-latency-99 baseline=0.004969 peak=0.009775 signed_z=630.67 onset_bin=33 onset_rel_s=753.75 persistence_bins=29
values_compact=delta:0.004972,-0.000006,0.000005,0,-0.000011,0.000017,0.000005,-0.000016,0.000006,0,-0.000012,0.000006,0.000012,-0.000001,-0.000006,-0.000006,-0.000005,0,0,0,0,0,0,0.000018,0.000012,-0.000018,-0.000012,0.000006,0.000012,-0.000007,-0.000011,0.000012,0.000005,0.000019,0.000675,-0.000696,0.004251,0.000003,-0.000794,0.00049,-0.00065,-0.000623,0.001422,0.000243,-0.000247,-0.000381,0.000439,0.000642,-0.000634,-0.00093,0.0009,0.000084,-0.001294,0.000229,-0.000411,-0.002733,0.001719,0.002539,0.000042,-0.000644,0.000442,0.000081,-0.000034,-0.000106
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M10] rank=10 service=currencyservice metric=istio-bytes-90 baseline=0.244463 peak=0.098008 signed_z=-616.334 onset_bin=40 onset_rel_s=911.25 persistence_bins=23
values_compact=raw:[0.244346,0.244553,0.244491,0.244481,0.244387,0.244313,0.244493,0.24454,0.244367,0.244526,0.244479,0.244464,0.244453,0.24445,0.24457,0.244544,0.244414,0.244329,0.244608,0.244584,0.244581,0.244475,0.244469,0.244509,0.244551,0.244524,0.244429,0.244309,0.244329,0.244465,0.24465,0.244465,0.244509,0.244602,0.239364,0.244887,0.242284,0.244036,0.242836,0.24465,0.098268,0.098389,0.222761,0.225146,0.245059,0.09843,0.098416,0.09859,0.09854,0.098495,0.098496,0.09834,0.098314,0.098514,0.098524,0.098501,0.09847,0.23567,0.234453,0.098048,0.098139,0.098454,0.098382,0.245477]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M11] rank=11 service=frontend metric=istio-latency-95 baseline=0.13331 peak=25.49 signed_z=566.571 onset_bin=32 onset_rel_s=731.25 persistence_bins=32
values_compact=raw:[0.099658,0.097255,0.126316,0.153639,0.099016,0.099612,0.099973,0.096171,0.09432,0.093956,0.096446,0.098539,0.160652,0.136466,0.095948,0.098343,0.214718,0.22,0.123662,0.213455,0.199188,0.09811,0.1225,0.132958,0.185263,0.182597,0.098453,0.177143,0.20832,0.098357,0.096576,0.097329,0.470679,2.311058,3.813989,4.224138,6.096774,4.383621,3.232692,3.8625,2.357377,2.265183,8.727273,8.659091,2.373684,2.174107,3.259375,25.49,21.439973,2.44,3.709815,18.071429,15.057143,2.794444,7.922414,7.287037,2.809783,3.480634,3.453704,2.483548,4.523148,6.017857,7.376437,6.899306]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M12] rank=12 service=checkoutservice metric=istio-latency-50 baseline=0.04237 peak=0.916667 signed_z=466.637 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=raw:[0.045312,0.04197,0.040417,0.041159,0.040833,0.040313,0.040323,0.042188,0.044886,0.042803,0.044286,0.046983,0.0425,0.040132,0.040278,0.040441,0.045076,0.045221,0.042361,0.042308,0.041827,0.042857,0.043421,0.04099,0.041429,0.042568,0.042647,0.043382,0.041071,0.040625,0.041554,0.043452,0.046875,0.060714,0.3,0.666667,0.375,0.34375,0.357143,0.359375,0.409091,0.354167,0.428571,0.772727,0.520833,0.270833,0.5,0.541667,0.390625,0.36875,0.361112,0.247794,0.228571,0.513889,0.5,0.375,0.20625,0.19375,0.303571,0.385417,0.443182,0.775,0.875,0.604167]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[988.0,1140.0]

=== LOG SUMMARY ===
{"entries":[{"error_logs":24,"error_pct":0.04,"service":"frontend","total_logs":57746}],"mode":"errors","omitted_services":9,"service_count":10}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":758.8,"error_pct":0.0,"p95_during_ms":63.92964999999987,"p95_pre_ms":7.444399999999994,"service":"recommendationservice","spans":24548},{"delta_pct":347.5,"error_pct":0.0,"p95_during_ms":357.5616999999997,"p95_pre_ms":79.89579999999998,"service":"checkoutservice","spans":8112},{"delta_pct":254.8,"error_pct":0.0,"p95_during_ms":832.2345999999998,"p95_pre_ms":234.53294999999997,"service":"frontend","spans":186481},{"delta_pct":37.4,"error_pct":0.0,"p95_during_ms":0.2995999999999999,"p95_pre_ms":0.218,"service":"currencyservice","spans":51925},{"delta_pct":12.0,"error_pct":0.0,"p95_during_ms":0.028,"p95_pre_ms":0.025,"service":"productcatalogservice","spans":92203},{"delta_pct":-11.8,"error_pct":0.0,"p95_during_ms":0.40199999999999997,"p95_pre_ms":0.45559999999999995,"service":"emailservice","spans":1164},{"delta_pct":9.6,"error_pct":0.0,"p95_during_ms":0.4357,"p95_pre_ms":0.39739999999999975,"service":"paymentservice","spans":876}],"omitted_services":0,"service_count":7}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=3 omitted_edges=0
[{"evidence_source":"metric","onset_rel_s":769.8,"rank":1,"service":"recommendationservice","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":799.8,"rank":2,"service":"adservice","severity_z":630.67},{"evidence_source":"metric","onset_rel_s":874.8,"rank":3,"service":"productcatalogservice","severity_z":120.73},{"evidence_source":"metric","onset_rel_s":934.8,"rank":4,"service":"frontend-external","severity_z":181.204},{"evidence_source":"metric","onset_rel_s":949.8,"rank":5,"service":"currencyservice","severity_z":999.0},{"evidence_source":"trace","onset_rel_s":1035.0,"rank":6,"service":"frontend","severity_z":57.559},{"evidence_source":"metric","onset_rel_s":1047.0,"rank":7,"service":"emailservice","severity_z":42.272},{"evidence_source":"metric","onset_rel_s":1062.0,"rank":8,"service":"shippingservice","severity_z":87.509},{"evidence_source":"metric","onset_rel_s":1063.8,"rank":9,"service":"paymentservice","severity_z":79.462},{"evidence_source":"metric","onset_rel_s":1204.8,"rank":10,"service":"cartservice","severity_z":47.586},{"evidence_source":"trace","onset_rel_s":1365.0,"rank":11,"service":"checkoutservice","severity_z":6.911},{"evidence_source":"none","onset_rel_s":null,"rank":12,"service":"gke-gke-cluster-default-pool-2e1807ce-cx8g","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":13,"service":"redis","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":14,"service":"loadgenerator","severity_z":0.0}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"currencyservice","caller":"checkoutservice"},{"callee":"emailservice","caller":"checkoutservice"},{"callee":"paymentservice","caller":"checkoutservice"},{"callee":"productcatalogservice","caller":"checkoutservice"},{"callee":"checkoutservice","caller":"frontend"},{"callee":"currencyservice","caller":"frontend"},{"callee":"productcatalogservice","caller":"frontend"},{"callee":"recommendationservice","caller":"frontend"},{"callee":"productcatalogservice","caller":"recommendationservice"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

{"confidence":"high","reason":"Rank currencyservice first because currencyservice has direct istio-latency-50 evidence (signed-z 999, persistence 31 bins); although frontend is salient, the caller path frontend -> currencyservice means a disturbance in the callee can propagate back toward that caller-side symptom.","services":["currencyservice","frontend"]}

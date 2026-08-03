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
opaque_id: INC-418060F933F2
observation_window={"duration_rel_s":1440.0,"source_metric_rows":1441}
selection_summary={"candidate_count":17,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":256,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["adservice","cartservice","checkoutservice","currencyservice","emailservice","frontend","frontend-external","gke-gke-cluster-default-pool-2e1807ce-0e4z","gke-gke-cluster-default-pool-2e1807ce-cx8g","gke-gke-cluster-default-pool-2e1807ce-w819","gke-gke-cluster-default-pool-2e1807ce-xte3","loadgenerator","paymentservice","productcatalogservice","recommendationservice","redis","shippingservice"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[11.25,33.75,56.25,78.75,101.25,123.75,146.25,168.75,191.25,213.75,236.25,258.75,281.25,303.75,326.25,348.75,371.25,393.75,416.25,438.75,461.25,483.75,506.25,528.75,551.25,573.75,596.25,618.75,641.25,663.75,686.25,708.75,731.25,753.75,776.25,798.75,821.25,843.75,866.25,888.75,911.25,933.75,956.25,978.75,1001.25,1023.75,1046.25,1068.75,1091.25,1113.75,1136.25,1158.75,1181.25,1203.75,1226.25,1248.75,1271.25,1293.75,1316.25,1338.75,1361.25,1383.75,1406.25,1428.75]
[M1] rank=1 service=currencyservice metric=istio-latency-50 baseline=0.003202 peak=0.107315 signed_z=999.0 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=raw:[0.003213,0.003167,0.003269,0.003275,0.003196,0.003261,0.003183,0.003112,0.003198,0.003195,0.003119,0.003116,0.003203,0.003227,0.003166,0.003129,0.003115,0.003179,0.003288,0.003238,0.003241,0.003273,0.00318,0.00315,0.00321,0.003218,0.003313,0.003314,0.003176,0.003164,0.003199,0.003203,0.003203,0.003609,0.101592,0.100467,0.102383,0.102581,0.102645,0.102876,0.103107,0.103135,0.101202,0.100799,0.101664,0.102007,0.101999,0.10205,0.101751,0.101359,0.100731,0.101088,0.101592,0.102233,0.102852,0.102471,0.101027,0.101336,0.10155,0.102005,0.101862,0.101603,0.101368,0.101036]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M2] rank=2 service=cartservice metric=istio-latency-95 baseline=0.004986 peak=0.305469 signed_z=999.0 onset_bin=45 onset_rel_s=1023.75 persistence_bins=3
values_compact=raw:[0.006273,0.005345,0.004973,0.005463,0.004977,0.004917,0.004894,0.004886,0.004902,0.004898,0.004871,0.00488,0.004939,0.004925,0.004893,0.00489,0.004907,0.004958,0.004957,0.004915,0.004908,0.004915,0.004875,0.004852,0.004885,0.004897,0.004927,0.004939,0.0049,0.004871,0.004901,0.004914,0.004907,0.004932,0.004934,0.004937,0.004926,0.004925,0.004945,0.004905,0.004932,0.004928,0.004899,0.004892,0.004995,0.006726,0.008688,0.006804,0.004905,0.004927,0.004911,0.004956,0.00496,0.004908,0.004914,0.004901,0.004927,0.004986,0.004983,0.004944,0.004896,0.004882,0.004913,0.004979]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M3] rank=3 service=cartservice metric=istio-latency-99 baseline=0.008425 peak=0.863382 signed_z=999.0 onset_bin=44 onset_rel_s=1001.25 persistence_bins=8
values_compact=raw:[0.009361,0.009207,0.009173,0.009482,0.009119,0.008526,0.007921,0.007964,0.008417,0.008132,0.007283,0.00768,0.009051,0.008848,0.008277,0.00821,0.008621,0.009162,0.008822,0.008602,0.008689,0.00873,0.00765,0.006311,0.007722,0.007987,0.008547,0.009354,0.009369,0.007676,0.008185,0.008717,0.008513,0.008513,0.008535,0.009073,0.008937,0.008588,0.008854,0.008411,0.008506,0.008464,0.008023,0.007909,0.653846,0.745833,0.765,0.694375,0.008394,0.008681,0.009835,0.59875,0.01915,0.008196,0.008408,0.008209,0.009096,0.014598,0.011083,0.008739,0.007967,0.00763,0.008263,0.008974]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M4] rank=4 service=checkoutservice metric=istio-latency-50 baseline=0.042999 peak=1.2625 signed_z=559.127 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=raw:[0.044712,0.04375,0.04375,0.04212,0.041288,0.041159,0.0425,0.045833,0.04,0.044375,0.045536,0.042949,0.044595,0.046667,0.041406,0.039015,0.045,0.044355,0.041447,0.042361,0.045161,0.046121,0.043382,0.041223,0.039583,0.041667,0.044444,0.043981,0.0445,0.042708,0.0405,0.04,0.040625,0.07,0.59375,0.775,0.711538,0.605263,0.571429,1.15,1.044118,0.777778,0.721154,0.684783,0.693182,0.819444,0.8125,0.75,0.684211,0.611111,0.75,0.9375,0.925,0.71875,0.490385,0.659091,0.605263,0.659091,0.8,0.625,0.492188,0.517857,0.478448,0.472222]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M5] rank=5 service=frontend metric=istio-latency-90 baseline=0.090476 peak=1.954894 signed_z=499.439 onset_bin=32 onset_rel_s=731.25 persistence_bins=32
values_compact=raw:[0.090655,0.087089,0.097018,0.097937,0.08854,0.090015,0.087348,0.084804,0.090082,0.087573,0.085186,0.086932,0.093232,0.095196,0.086941,0.082902,0.086136,0.091686,0.094341,0.091017,0.091541,0.093244,0.088559,0.086892,0.089707,0.090016,0.097516,0.097695,0.091898,0.090541,0.091821,0.093825,0.107969,0.873729,1.879358,1.874893,1.836512,1.823944,1.92887,1.937342,1.848157,1.802392,1.594199,1.626374,1.867358,1.812428,1.704386,1.715318,1.75375,1.806164,1.839462,1.805714,1.845581,1.875,1.80198,1.794472,1.704381,1.697382,1.75,1.75303,1.79875,1.764439,1.559091,1.591379]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M6] rank=6 service=frontend metric=istio-latency-50 baseline=0.04122 peak=0.433973 signed_z=410.03 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=raw:[0.041836,0.041269,0.042696,0.04275,0.041363,0.041159,0.040016,0.039446,0.039681,0.039504,0.040326,0.041104,0.041975,0.041994,0.0405,0.039356,0.039965,0.041353,0.041476,0.041486,0.041898,0.041562,0.040905,0.041112,0.041695,0.041474,0.042086,0.042554,0.042198,0.041969,0.040835,0.041507,0.043905,0.06052,0.416129,0.418778,0.423259,0.420619,0.426049,0.423611,0.414014,0.416327,0.412428,0.413845,0.417595,0.416041,0.427906,0.423596,0.422405,0.427463,0.4266,0.426438,0.42043,0.422632,0.419662,0.422009,0.425,0.419588,0.416403,0.413848,0.412446,0.417644,0.424035,0.428496]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M7] rank=7 service=currencyservice metric=istio-latency-90 baseline=0.005224 peak=0.226418 signed_z=396.076 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=raw:[0.004983,0.004901,0.00605,0.006149,0.004953,0.005877,0.004929,0.004801,0.004957,0.004951,0.004814,0.004808,0.004965,0.005142,0.004898,0.004832,0.004807,0.004923,0.006187,0.005311,0.005407,0.005995,0.004924,0.00487,0.004979,0.004993,0.006865,0.00681,0.004918,0.004896,0.004958,0.004965,0.004965,0.175105,0.225411,0.221811,0.222944,0.222988,0.225105,0.225176,0.224862,0.224926,0.221842,0.221645,0.223157,0.223386,0.223763,0.223858,0.223867,0.223678,0.222565,0.222631,0.222711,0.222754,0.224813,0.224859,0.222018,0.222119,0.223131,0.223139,0.222881,0.222796,0.222541,0.222392]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M8] rank=8 service=emailservice metric=container-sockets baseline=3.0 peak=4.0 signed_z=250.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=rle:3*64
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M9] rank=9 service=currencyservice metric=istio-latency-95 baseline=0.007521 peak=0.241961 signed_z=216.801 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=raw:[0.007441,0.006785,0.008861,0.008938,0.007349,0.00872,0.007835,0.00528,0.008245,0.008199,0.005557,0.005433,0.008199,0.008523,0.006809,0.005883,0.005409,0.007347,0.008467,0.007706,0.008175,0.008459,0.007037,0.006448,0.007407,0.00752,0.009502,0.009356,0.00693,0.00673,0.008044,0.008067,0.008463,0.217909,0.240889,0.236979,0.238014,0.238029,0.240368,0.240464,0.240142,0.240114,0.236923,0.236813,0.238344,0.238541,0.238983,0.239084,0.239171,0.238967,0.237794,0.237854,0.23785,0.237819,0.240058,0.240158,0.237246,0.237308,0.238254,0.238282,0.238041,0.237951,0.237687,0.237561]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M10] rank=10 service=checkoutservice metric=istio-latency-90 baseline=0.084821 peak=2.2525 signed_z=166.58 onset_bin=20 onset_rel_s=461.25 persistence_bins=33
values_compact=raw:[0.086333,0.085,0.08675,0.085667,0.081667,0.077917,0.0825,0.0875,0.07,0.085909,0.087222,0.085294,0.09,0.092,0.079,0.05375,0.086667,0.085882,0.079167,0.082143,0.125,0.1325,0.084375,0.078214,0.065,0.08,0.095,0.089375,0.086071,0.083,0.079,0.078,0.0875,0.916667,1.7125,2.065,1.975,1.6375,1.95,2.23,2.208824,2.04,1.91,1.1125,0.993182,2.05,2.05,1.6,1.685714,1.5,1.915,2.17,2.173529,2.103571,1.95625,1.825,1.557143,1.825,2.061538,1.75,1.57,1.69375,0.992105,0.976471]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M11] rank=11 service=checkoutservice metric=istio-latency-95 baseline=0.099856 peak=2.37625 signed_z=93.9 onset_bin=20 onset_rel_s=461.25 persistence_bins=34
values_compact=raw:[0.093167,0.0925,0.094625,0.09625,0.093611,0.088958,0.09125,0.09375,0.085,0.092955,0.093611,0.092647,0.097632,0.0985,0.0895,0.076875,0.093333,0.092941,0.089583,0.091071,0.1875,0.19125,0.092188,0.089107,0.0825,0.09,0.145,0.099792,0.093036,0.0915,0.0945,0.099,0.2125,1.375,2.10625,2.2825,2.2375,2.06875,2.225,2.365,2.354412,2.27,2.205,1.80625,1.675,2.275,2.275,2.05,2.092857,2.0,2.2075,2.335,2.336765,2.301786,2.228125,2.1625,2.028571,2.1625,2.280769,2.125,2.035,2.096875,1.705,1.6]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M12] rank=12 service=frontend metric=istio-latency-95 baseline=0.118487 peak=2.268936 signed_z=71.546 onset_bin=32 onset_rel_s=731.25 persistence_bins=32
values_compact=raw:[0.098948,0.095418,0.180822,0.18625,0.097294,0.099289,0.097936,0.095735,0.124643,0.098912,0.094301,0.095247,0.142857,0.170205,0.09575,0.092555,0.095749,0.113413,0.152917,0.099826,0.099851,0.141184,0.097246,0.095242,0.098226,0.09904,0.190521,0.188462,0.105357,0.099099,0.134432,0.153517,0.414826,1.688393,2.210321,2.193884,2.196163,2.190141,2.245816,2.250316,2.201728,2.179904,2.047099,2.063187,2.238083,2.216908,2.146053,2.151012,2.149375,2.17363,2.173094,2.16,2.190233,2.201014,2.165842,2.162312,2.102191,2.098691,2.132937,2.134091,2.179375,2.164305,2.038636,2.05431]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[990.0,1140.0]

=== LOG SUMMARY ===
{"entries":[{"change_pct":-89.6,"n_during":944,"n_pre":9099,"service":"adservice"},{"change_pct":-89.6,"n_during":182,"n_pre":1753,"service":"checkoutservice"},{"change_pct":-89.6,"n_during":61,"n_pre":584,"service":"emailservice"},{"change_pct":-89.6,"n_during":122,"n_pre":1168,"service":"paymentservice"},{"change_pct":-89.5,"n_during":5709,"n_pre":54413,"service":"frontend"},{"change_pct":-89.3,"n_during":1657,"n_pre":15551,"service":"cartservice"},{"change_pct":-89.3,"n_during":1203,"n_pre":11225,"service":"recommendationservice"},{"change_pct":-89.0,"n_during":994,"n_pre":9068,"service":"shippingservice"}],"mode":"volume","omitted_services":1,"service_count":9}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":211.2,"error_pct":0.0,"p95_during_ms":639.7460999999998,"p95_pre_ms":205.60455,"service":"checkoutservice","spans":8820},{"delta_pct":114.2,"error_pct":0.0,"p95_during_ms":440.7674,"p95_pre_ms":205.76765,"service":"frontend","spans":193297},{"delta_pct":31.3,"error_pct":0.0,"p95_during_ms":0.48650000000000004,"p95_pre_ms":0.3704499999999992,"service":"paymentservice","spans":933},{"delta_pct":5.4,"error_pct":0.0,"p95_during_ms":4.63025,"p95_pre_ms":4.392,"service":"recommendationservice","spans":25435},{"delta_pct":1.6,"error_pct":0.0,"p95_during_ms":0.425,"p95_pre_ms":0.41814999999999986,"service":"emailservice","spans":1221},{"delta_pct":-0.6,"error_pct":0.0,"p95_during_ms":0.173,"p95_pre_ms":0.174,"service":"currencyservice","spans":54132},{"delta_pct":0.0,"error_pct":0.0,"p95_during_ms":0.024,"p95_pre_ms":0.024,"service":"productcatalogservice","spans":95394}],"omitted_services":0,"service_count":7}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=3 omitted_edges=0
[{"evidence_source":"metric","onset_rel_s":757.2,"rank":1,"service":"frontend","severity_z":499.439},{"evidence_source":"metric","onset_rel_s":772.2,"rank":2,"service":"currencyservice","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":778.8,"rank":3,"service":"checkoutservice","severity_z":559.127},{"evidence_source":"metric","onset_rel_s":784.2,"rank":4,"service":"shippingservice","severity_z":18.65},{"evidence_source":"metric","onset_rel_s":850.8,"rank":5,"service":"emailservice","severity_z":250.0},{"evidence_source":"metric","onset_rel_s":985.8,"rank":6,"service":"gke-gke-cluster-default-pool-2e1807ce-0e4z","severity_z":10.347},{"evidence_source":"metric","onset_rel_s":1030.8,"rank":7,"service":"cartservice","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1392.0,"rank":8,"service":"gke-gke-cluster-default-pool-2e1807ce-xte3","severity_z":39.344},{"evidence_source":"metric","onset_rel_s":1408.8,"rank":9,"service":"paymentservice","severity_z":37.927},{"evidence_source":"none","onset_rel_s":null,"rank":10,"service":"recommendationservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":11,"service":"productcatalogservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":12,"service":"adservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":13,"service":"gke-gke-cluster-default-pool-2e1807ce-w819","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":14,"service":"loadgenerator","severity_z":0.0}]
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

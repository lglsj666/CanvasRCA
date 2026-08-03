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
opaque_id: INC-3C5E569313A5
observation_window={"duration_rel_s":1440.0,"source_metric_rows":1441}
selection_summary={"candidate_count":16,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":265,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["adservice","cartservice","checkoutservice","currencyservice","emailservice","frontend","frontend-external","gke-gke-cluster-default-pool-9da84637-9mfj","gke-gke-cluster-default-pool-9da84637-rkn0","gke-gke-cluster-default-pool-9da84637-x97r","loadgenerator","paymentservice","productcatalogservice","recommendationservice","redis","shippingservice"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[11.25,33.75,56.25,78.75,101.25,123.75,146.25,168.75,191.25,213.75,236.25,258.75,281.25,303.75,326.25,348.75,371.25,393.75,416.25,438.75,461.25,483.75,506.25,528.75,551.25,573.75,596.25,618.75,641.25,663.75,686.25,708.75,731.25,753.75,776.25,798.75,821.25,843.75,866.25,888.75,911.25,933.75,956.25,978.75,1001.25,1023.75,1046.25,1068.75,1091.25,1113.75,1136.25,1158.75,1181.25,1203.75,1226.25,1248.75,1271.25,1293.75,1316.25,1338.75,1361.25,1383.75,1406.25,1428.75]
[M1] rank=1 service=recommendationservice metric=istio-latency-50 baseline=0.006846 peak=45.0 signed_z=999.0 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=raw:[0.007117,0.007143,0.007076,0.006958,0.006895,0.006969,0.007008,0.006939,0.006917,0.006829,0.00673,0.006657,0.006699,0.006733,0.006676,0.006624,0.006572,0.006523,0.006596,0.006613,0.006566,0.006672,0.006751,0.007037,0.007248,0.007152,0.007056,0.006991,0.006891,0.006813,0.00683,0.006792,0.006862,0.008406,0.143561,1.100937,0.584466,0.146446,0.204819,0.180432,0.181522,0.241226,0.289474,0.168931,0.143569,0.158467,0.208434,0.200877,0.142458,0.165405,0.179891,0.249783,0.28,0.184375,45.0,45.0,45.0,0.410714,0.248077,0.243643,0.226562,0.25078,0.326389,0.220703]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,11,19,22,4,11,23,22,23,22,23,23
[M2] rank=2 service=frontend metric=istio-latency-90 baseline=0.144748 peak=53.58 signed_z=999.0 onset_bin=33 onset_rel_s=753.75 persistence_bins=29
values_compact=raw:[0.220228,0.215286,0.178202,0.171839,0.159884,0.098726,0.121885,0.132126,0.098549,0.103792,0.165143,0.181038,0.146373,0.127217,0.136166,0.120646,0.10996,0.122391,0.139386,0.138099,0.135396,0.142707,0.099347,0.109663,0.125878,0.121539,0.2335,0.222724,0.096618,0.117495,0.180429,0.150685,0.151968,0.499828,0.992857,12.840909,9.605769,1.348403,1.707143,1.606341,0.948264,1.294901,2.483735,2.04125,0.831098,0.674691,0.915646,1.0445,1.351562,1.157946,0.954962,1.663804,1.66,0.838248,50.94,34.755,0.171471,0.14592,0.934762,1.408254,1.876087,2.124436,1.913421,1.398889]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M3] rank=3 service=productcatalogservice metric=istio-latency-90 baseline=0.004274 peak=0.027153 signed_z=999.0 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=delta:0.004337,-0.000019,-0.000034,0.000001,-0.000003,-0.000013,0,0,-0.000007,0.000002,0.000011,-0.000005,-0.000003,-0.000003,-0.000005,-0.000003,0.000008,-0.000005,-0.000002,0.000012,0.000001,0,-0.000002,-0.000002,0.000018,-0.000011,0.000015,0,-0.000032,0,0.000017,0.000012,-0.000001,0.000204,0.0002,0.001617,-0.001313,-0.000434,0.00006,-0.000033,-0.000105,0.000122,-0.000006,0.000122,0.000101,-0.000368,0.000162,0.0001,-0.000036,-0.000187,0.000077,0.00029,0.000117,-0.000061,0.020643,-0.007857,-0.013315,0.000049,0.000175,-0.000014,0.000127,0.000021,-0.000064,0.00004
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M4] rank=4 service=recommendationservice metric=istio-latency-90 baseline=0.009466 peak=57.0 signed_z=999.0 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=raw:[0.009597,0.009569,0.009565,0.009579,0.009516,0.009472,0.009473,0.009455,0.009442,0.009415,0.009413,0.009422,0.009382,0.009375,0.009376,0.009369,0.009361,0.009331,0.009331,0.00939,0.009461,0.009464,0.009403,0.009467,0.009504,0.009544,0.009725,0.009653,0.009477,0.009463,0.009506,0.00944,0.0094,0.515625,1.523295,12.522179,18.586219,1.584763,2.041667,1.853056,0.870588,1.746101,3.823529,2.335502,0.877797,0.846658,1.288462,1.59162,1.701497,1.24765,1.126923,2.054542,1.95,1.934091,57.0,57.0,57.0,2.017857,1.522414,2.130114,2.965116,2.190389,2.121667,1.771774]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,11,19,22,4,11,23,22,23,22,23,23
[M5] rank=5 service=productcatalogservice metric=istio-latency-95 baseline=0.00464 peak=0.038576 signed_z=999.0 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=delta:0.004676,-0.00001,-0.000016,0.000002,-0.000003,-0.000012,0,0,-0.000004,0.000001,0.000005,-0.000003,-0.000001,-0.000001,-0.000002,0,0.000002,-0.000003,0.000002,0.000006,0.000001,0.000001,-0.000003,-0.000003,0.000009,-0.000005,0.000007,-0.000001,-0.000016,0,0.000008,0.000008,0,0.000182,0.00075,0.00351,-0.000483,-0.003728,0.000068,-0.000042,-0.000132,0.000137,0.000009,0.001694,0.001307,-0.003139,0.000159,0.001149,-0.001095,-0.000197,0.000083,0.001843,0.000967,-0.000112,0.030203,-0.013233,-0.019849,0.00008,0.000127,0.000003,0.001362,-0.000073,-0.001224,0.000295
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M6] rank=6 service=recommendationservice metric=istio-latency-95 baseline=0.00993 peak=58.5 signed_z=999.0 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=raw:[0.009907,0.009872,0.009877,0.009907,0.009844,0.009785,0.009781,0.009769,0.009758,0.009738,0.009749,0.009768,0.009717,0.009705,0.009714,0.009712,0.00971,0.009682,0.009673,0.009737,0.009822,0.009813,0.009734,0.009771,0.009786,0.009843,0.012797,0.011876,0.0098,0.009794,0.009841,0.009771,0.009718,0.788644,2.515086,21.787634,24.29311,3.49271,3.315217,3.244565,1.121429,2.332011,6.730769,4.781879,1.289423,1.326373,2.355769,2.421159,2.410629,1.894025,2.217308,2.656351,2.303125,2.3875,58.5,58.5,58.5,2.3125,2.037069,3.173958,3.982558,3.067369,2.435833,2.220565]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,11,19,22,4,11,23,22,23,22,23,23
[M7] rank=7 service=productcatalogservice metric=istio-latency-99 baseline=0.004934 peak=4.794167 signed_z=999.0 onset_bin=33 onset_rel_s=753.75 persistence_bins=30
values_compact=delta:0.004948,-0.000004,-0.000003,0.000005,-0.000003,-0.000009,-0.000003,0.000001,-0.000001,0,0,-0.000002,0.000001,0,0.000001,0.000001,-0.000001,-0.000002,0.000004,0.000003,0.000001,0,-0.000003,-0.000004,0.000002,0,0.000001,-0.000003,-0.000002,0,0.000001,0.000005,0,0.218806,0.099348,2.400841,-0.178929,-2.535601,-0.000054,-0.000217,-0.003998,0.003589,0.000091,0.288373,0.25927,-0.549899,0.002295,0.373211,0.367889,-0.743135,0.001528,0.001301,0.00262,0.012032,0.023261,-0.002929,-0.039681,0.001754,0.001853,0.004987,0.013691,-0.009138,-0.009203,0.000163
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M8] rank=8 service=recommendationservice metric=istio-latency-99 baseline=0.01543 peak=59.7 signed_z=999.0 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=raw:[0.021433,0.020189,0.020025,0.02079,0.01928,0.015331,0.014592,0.013262,0.0154,0.012916,0.013045,0.015686,0.009986,0.009969,0.009984,0.009986,0.009989,0.009962,0.009946,0.012318,0.019109,0.018493,0.009999,0.013469,0.013225,0.017763,0.028278,0.023996,0.017134,0.015178,0.01928,0.014574,0.009971,1.651567,4.503017,28.357527,28.858622,5.698542,4.923913,4.909783,2.224286,4.3,9.346154,8.995259,3.282813,3.029477,4.421875,4.437698,4.427899,3.354702,4.325,4.497979,3.87,4.335,59.7,59.7,59.7,3.625,2.448793,4.634792,4.796512,4.613474,4.371667,3.675]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,11,19,22,4,11,23,22,23,22,23,23
[M9] rank=9 service=cartservice metric=istio-bytes-90 baseline=0.247269 peak=1.383333 signed_z=999.0 onset_bin=53 onset_rel_s=1203.75 persistence_bins=3
values_compact=raw:[0.247938,0.247414,0.247322,0.247199,0.24715,0.247365,0.247351,0.247285,0.247162,0.247438,0.24731,0.247372,0.247306,0.247326,0.247326,0.247131,0.247214,0.247343,0.247283,0.247251,0.247318,0.247331,0.24731,0.247285,0.24703,0.247376,0.247247,0.247082,0.247202,0.247367,0.247308,0.247318,0.247273,0.247042,0.247042,0.247548,0.247548,0.247247,0.247169,0.247216,0.247226,0.247318,0.247341,0.247247,0.247273,0.247236,0.247358,0.247334,0.247273,0.24721,0.247261,0.247261,0.24683,0.244986,0.243,0.248262,0.246785,0.247435,0.247141,0.247356,0.247843,0.246881,0.246941,0.247627]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M10] rank=10 service=currencyservice metric=istio-bytes-90 baseline=0.244543 peak=1.3375 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=raw:[0.245297,0.244371,0.244342,0.244606,0.244674,0.244321,0.243958,0.244585,0.244815,0.244574,0.244464,0.244494,0.244778,0.24431,0.244416,0.244568,0.244163,0.244302,0.244508,0.244477,0.244526,0.244523,0.244626,0.244498,0.244447,0.24445,0.244444,0.244564,0.244401,0.244508,0.244711,0.244428,0.244233,0.244312,0.244594,0.244866,0.244512,0.244491,0.244214,0.244389,0.24438,0.244538,0.244413,0.244463,0.244413,0.244414,0.244374,0.244767,0.244392,0.244392,0.244632,0.244551,0.245314,0.246108,0.242599,0.243713,0.244249,0.24456,0.244361,0.244267,0.244586,0.244371,0.244578,0.244403]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M11] rank=11 service=productcatalogservice metric=istio-bytes-90 baseline=0.245706 peak=1.558333 signed_z=999.0 onset_bin=39 onset_rel_s=888.75 persistence_bins=19
values_compact=raw:[0.245023,0.245004,0.245721,0.245708,0.245702,0.245661,0.245699,0.245948,0.245825,0.245927,0.245605,0.245681,0.245626,0.245459,0.245829,0.245921,0.24526,0.245432,0.246223,0.245753,0.245601,0.245747,0.245761,0.24585,0.24546,0.24575,0.245871,0.245513,0.245683,0.246081,0.245604,0.245506,0.245917,0.245571,0.247147,0.242344,0.244861,0.24768,0.247015,0.247242,0.24719,0.247305,0.247511,0.246699,0.244806,0.247411,0.247586,0.246405,0.245975,0.247169,0.247778,0.247351,0.248666,1.270637,0.243143,0.242678,0.243389,0.245272,0.24556,0.247176,0.247475,0.247817,0.248312,0.247403]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M12] rank=12 service=frontend metric=istio-latency-95 baseline=0.218274 peak=56.79 signed_z=827.732 onset_bin=26 onset_rel_s=596.25 persistence_bins=31
values_compact=raw:[0.246042,0.245491,0.227584,0.235,0.226453,0.176311,0.196393,0.199686,0.170444,0.177836,0.213571,0.224798,0.20701,0.192129,0.194923,0.186905,0.17998,0.187285,0.19557,0.194049,0.200252,0.214518,0.185679,0.179831,0.189084,0.193001,0.507,0.463964,0.164604,0.193706,0.233409,0.21205,0.211145,0.775061,2.138889,21.420455,19.534091,3.084509,2.472477,2.466053,1.775,2.120587,5.5,5.383333,1.141176,0.911844,1.873214,2.100119,2.208418,2.019196,1.909868,2.312995,2.28,1.478953,55.47,47.3775,0.229363,0.226081,1.817593,2.320898,3.271667,3.08882,2.340921,2.027907]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[1181.0,1316.0]

=== LOG SUMMARY ===
{"entries":[{"error_logs":961,"error_pct":1.6,"service":"frontend","total_logs":60137},{"error_logs":4,"error_pct":0.03,"service":"recommendationservice","total_logs":11578}],"mode":"errors","omitted_services":8,"service_count":10}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":176.4,"error_pct":0.0,"p95_during_ms":1485.7258000000002,"p95_pre_ms":537.5155499999975,"service":"recommendationservice","spans":23343},{"delta_pct":26.3,"error_pct":0.0,"p95_during_ms":0.024,"p95_pre_ms":0.019,"service":"productcatalogservice","spans":90138},{"delta_pct":23.1,"error_pct":0.0,"p95_during_ms":117.00594999999979,"p95_pre_ms":95.03244999999929,"service":"frontend","spans":187130},{"delta_pct":15.6,"error_pct":0.0,"p95_during_ms":0.23,"p95_pre_ms":0.199,"service":"currencyservice","spans":52387},{"delta_pct":10.2,"error_pct":0.0,"p95_during_ms":76.429,"p95_pre_ms":69.34109999999994,"service":"checkoutservice","spans":8760},{"delta_pct":8.1,"error_pct":0.0,"p95_during_ms":0.429,"p95_pre_ms":0.397,"service":"emailservice","spans":1213},{"delta_pct":2.9,"error_pct":0.0,"p95_during_ms":1.1095,"p95_pre_ms":1.078199999999999,"service":"paymentservice","spans":925}],"omitted_services":0,"service_count":7}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=2 omitted_edges=1
[{"evidence_source":"metric","onset_rel_s":769.2,"rank":1,"service":"frontend-external","severity_z":13.544},{"evidence_source":"metric","onset_rel_s":817.8,"rank":2,"service":"gke-gke-cluster-default-pool-9da84637-9mfj","severity_z":357.221},{"evidence_source":"metric","onset_rel_s":1183.2,"rank":3,"service":"gke-gke-cluster-default-pool-9da84637-rkn0","severity_z":13.622},{"evidence_source":"trace","onset_rel_s":1185.0,"rank":4,"service":"frontend","severity_z":85.654},{"evidence_source":"trace","onset_rel_s":1185.0,"rank":5,"service":"productcatalogservice","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1188.0,"rank":6,"service":"gke-gke-cluster-default-pool-9da84637-x97r","severity_z":14.728},{"evidence_source":"metric","onset_rel_s":1204.2,"rank":7,"service":"cartservice","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1204.2,"rank":8,"service":"adservice","severity_z":141.762},{"evidence_source":"metric","onset_rel_s":1215.0,"rank":9,"service":"currencyservice","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1219.2,"rank":10,"service":"recommendationservice","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1219.2,"rank":11,"service":"shippingservice","severity_z":383.652},{"evidence_source":"metric","onset_rel_s":1219.2,"rank":12,"service":"checkoutservice","severity_z":65.946},{"evidence_source":"metric","onset_rel_s":1221.0,"rank":13,"service":"emailservice","severity_z":72.681},{"evidence_source":"metric","onset_rel_s":1222.2,"rank":14,"service":"paymentservice","severity_z":79.247}]
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

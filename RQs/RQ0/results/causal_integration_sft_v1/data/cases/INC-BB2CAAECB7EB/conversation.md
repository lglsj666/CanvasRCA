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
opaque_id: INC-BB2CAAECB7EB
observation_window={"duration_rel_s":1440.0,"source_metric_rows":1441}
selection_summary={"candidate_count":17,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":262,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["adservice","cartservice","checkoutservice","currencyservice","emailservice","frontend","frontend-external","gke-gke-cluster-default-pool-2e1807ce-0e4z","gke-gke-cluster-default-pool-2e1807ce-cx8g","gke-gke-cluster-default-pool-2e1807ce-w819","gke-gke-cluster-default-pool-2e1807ce-xte3","loadgenerator","paymentservice","productcatalogservice","recommendationservice","redis","shippingservice"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[11.25,33.75,56.25,78.75,101.25,123.75,146.25,168.75,191.25,213.75,236.25,258.75,281.25,303.75,326.25,348.75,371.25,393.75,416.25,438.75,461.25,483.75,506.25,528.75,551.25,573.75,596.25,618.75,641.25,663.75,686.25,708.75,731.25,753.75,776.25,798.75,821.25,843.75,866.25,888.75,911.25,933.75,956.25,978.75,1001.25,1023.75,1046.25,1068.75,1091.25,1113.75,1136.25,1158.75,1181.25,1203.75,1226.25,1248.75,1271.25,1293.75,1316.25,1338.75,1361.25,1383.75,1406.25,1428.75]
[M1] rank=1 service=currencyservice metric=istio-latency-50 baseline=0.003206 peak=0.106341 signed_z=999.0 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=raw:[0.003293,0.003197,0.003176,0.003159,0.003139,0.003158,0.003161,0.003175,0.003169,0.003176,0.003164,0.003189,0.003214,0.003171,0.003154,0.003168,0.003153,0.003171,0.003213,0.003322,0.003427,0.003343,0.003278,0.003378,0.003329,0.003158,0.003127,0.003155,0.003167,0.00314,0.003178,0.003202,0.003231,0.004203,0.101665,0.103344,0.101161,0.100869,0.101247,0.10209,0.102994,0.101194,0.100707,0.085,0.1,0.100632,0.102016,0.101659,0.102144,0.102351,0.100543,0.100344,0.10121,0.100714,0.1,0.101417,0.102554,0.101256,0.100933,0.101108,0.10134,0.101618,0.102498,0.102296]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M2] rank=2 service=currencyservice metric=istio-latency-90 baseline=0.005279 peak=0.227326 signed_z=292.52 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=raw:[0.00619,0.004954,0.004917,0.004886,0.00485,0.004884,0.004891,0.004914,0.004904,0.004917,0.004895,0.00494,0.004986,0.004907,0.004877,0.004902,0.004876,0.004907,0.004983,0.006462,0.007418,0.006786,0.005957,0.007091,0.00672,0.004884,0.004829,0.004879,0.004901,0.004852,0.00492,0.004964,0.005198,0.200283,0.223301,0.224413,0.222656,0.221645,0.221366,0.223686,0.223968,0.223145,0.222968,0.220941,0.220892,0.222057,0.223468,0.223066,0.223182,0.223025,0.221267,0.22109,0.223187,0.222407,0.2207,0.223155,0.223521,0.22222,0.222478,0.222142,0.221303,0.223561,0.225157,0.224145]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M3] rank=3 service=currencyservice metric=istio-latency-95 baseline=0.00728 peak=0.242754 signed_z=277.668 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=raw:[0.008336,0.007359,0.006927,0.006667,0.006208,0.006649,0.006723,0.006955,0.007024,0.007241,0.006815,0.007389,0.007684,0.006944,0.006653,0.006898,0.006596,0.007027,0.007628,0.008359,0.009009,0.008706,0.008119,0.008867,0.008812,0.006745,0.005832,0.006686,0.00718,0.006358,0.007361,0.007787,0.007877,0.22586,0.238505,0.239527,0.237825,0.236968,0.236381,0.238635,0.239089,0.23849,0.23825,0.236331,0.236003,0.236941,0.238649,0.238242,0.238364,0.238109,0.236357,0.236184,0.238434,0.237886,0.235787,0.238189,0.238613,0.237503,0.237719,0.237271,0.236299,0.238834,0.240484,0.239608]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M4] rank=4 service=checkoutservice metric=istio-latency-50 baseline=0.044231 peak=0.875 signed_z=219.254 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=raw:[0.042308,0.046,0.042188,0.040217,0.042857,0.042568,0.041544,0.041912,0.042014,0.043103,0.042083,0.040556,0.040217,0.041033,0.041406,0.042593,0.043056,0.045,0.046528,0.045109,0.047368,0.058333,0.052632,0.04837,0.04569,0.044397,0.044828,0.045259,0.044907,0.043304,0.0425,0.04213,0.042339,0.06,0.480263,0.525,0.673077,0.642857,0.727273,0.769231,0.846154,0.772727,0.522727,0.609375,0.666667,0.684211,0.67,0.659091,0.529412,0.543478,0.685185,0.75,0.716667,0.673077,0.7,0.714286,0.722222,0.675,0.625,0.678571,0.75,0.722222,0.625,0.692308]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M5] rank=5 service=frontend metric=istio-latency-50 baseline=0.041842 peak=0.435714 signed_z=214.615 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=raw:[0.042201,0.041424,0.041359,0.04065,0.039438,0.039761,0.040188,0.040846,0.041422,0.041026,0.040972,0.0415,0.041474,0.040913,0.04044,0.04016,0.040915,0.042021,0.042793,0.043932,0.045987,0.045681,0.043762,0.045825,0.045909,0.042176,0.040614,0.04095,0.041602,0.040939,0.040776,0.040896,0.041211,0.073171,0.418828,0.419118,0.424474,0.418587,0.409848,0.412348,0.414851,0.417272,0.412933,0.40692,0.409091,0.424628,0.43046,0.414916,0.419625,0.424845,0.422459,0.412796,0.404342,0.412872,0.413084,0.409,0.413934,0.41879,0.417094,0.417808,0.428079,0.435682,0.430873,0.419057]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M6] rank=6 service=frontend metric=istio-latency-90 baseline=0.092318 peak=1.879435 signed_z=178.337 onset_bin=23 onset_rel_s=528.75 persistence_bins=33
values_compact=raw:[0.091423,0.08965,0.089244,0.088373,0.085892,0.086109,0.085463,0.087107,0.088739,0.087217,0.086429,0.088648,0.091027,0.091387,0.089951,0.091199,0.091529,0.091728,0.093209,0.094047,0.098291,0.097524,0.095151,0.1258,0.129538,0.092442,0.086233,0.08902,0.092726,0.088255,0.088163,0.089939,0.09327,0.951948,1.775592,1.754286,1.766429,1.755198,1.761823,1.823673,1.84026,1.830405,1.740816,1.628652,1.638764,1.74375,1.826066,1.770149,1.694221,1.750688,1.776027,1.668919,1.505629,1.518438,1.613333,1.725126,1.837391,1.859833,1.788009,1.773502,1.850216,1.857328,1.764789,1.751579]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M7] rank=7 service=frontend metric=istio-latency-95 baseline=0.117184 peak=2.19806 signed_z=64.411 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=raw:[0.099634,0.098385,0.097892,0.0975,0.096229,0.0962,0.094888,0.095779,0.097203,0.095928,0.094929,0.09707,0.102452,0.117283,0.099992,0.127991,0.122217,0.107364,0.124141,0.128594,0.192324,0.178547,0.140536,0.2017,0.203615,0.11,0.094555,0.097731,0.131875,0.097321,0.097093,0.098985,0.151226,1.697143,2.137796,2.127143,2.133214,2.127599,2.130911,2.165155,2.176623,2.168581,2.120408,2.064326,2.069382,2.121875,2.170142,2.142537,2.097111,2.125344,2.138014,2.084459,2.002815,2.009219,2.056667,2.112563,2.168696,2.183054,2.150792,2.142986,2.175108,2.190385,2.153521,2.165263]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M8] rank=8 service=currencyservice metric=istio-latency-99 baseline=0.014919 peak=0.493864 signed_z=54.221 onset_bin=30 onset_rel_s=686.25 persistence_bins=33
values_compact=raw:[0.015475,0.009739,0.009411,0.009483,0.009443,0.009489,0.009503,0.009511,0.009934,0.014187,0.009638,0.025792,0.009983,0.009546,0.009722,0.009774,0.009616,0.009935,0.00991,0.009876,0.02149,0.020751,0.009847,0.019153,0.02375,0.009751,0.009221,0.00978,0.021052,0.009863,0.044437,0.043563,0.011303,0.246323,0.303258,0.342826,0.24996,0.249228,0.248393,0.290347,0.322159,0.312742,0.292963,0.248643,0.248093,0.248878,0.315583,0.278864,0.285338,0.263819,0.248429,0.248258,0.292143,0.27,0.247857,0.249909,0.300135,0.24973,0.2499,0.249368,0.248295,0.337424,0.4015,0.403712]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M9] rank=9 service=emailservice metric=container-network-receive-bytes-total baseline=807.235603 peak=6698.687042 signed_z=44.32 onset_bin=55 onset_rel_s=1248.75 persistence_bins=2
values_compact=delta:958.036162,-234.830453,110.120491,176.632904,10.117079,-117.585525,-15.454074,-142.978448,154.297176,-213.824509,0,323.531105,-73.332202,-0.369722,-124.342637,0,-181.791861,-10.78353,118.54652,84.812351,-61.952204,-27.299876,112.300313,-27.109128,76.654881,0,-40.617271,49.971137,-130.651188,68.992935,-34.112643,-220.059883,247.733192,29.705431,-118.94907,54.371058,-28.20742,-98.519059,-4.079881,52.498421,117.345346,12.921579,-69.47331,11.463249,-56.223124,40.320271,25.740938,-19.711936,68.358139,85.480718,-36.449466,-46.343031,-128.053593,70.778917,6.318455,4582.132368,0,-4640.480621,-29.206167,0.416375,274.760807,-156.428379,25.554455,-103.901984
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M10] rank=10 service=checkoutservice metric=istio-latency-90 baseline=0.095655 peak=2.183333 signed_z=39.185 onset_bin=20 onset_rel_s=461.25 persistence_bins=33
values_compact=raw:[0.082,0.087647,0.081667,0.072,0.083333,0.082667,0.079545,0.080833,0.081154,0.083846,0.081364,0.074545,0.072,0.077308,0.079,0.082727,0.08375,0.086667,0.088077,0.086786,0.3125,0.3375,0.090526,0.08925,0.087368,0.085938,0.086471,0.086944,0.086563,0.084231,0.0825,0.0815,0.085,0.88,1.225,1.80625,1.8625,1.2,1.942857,2.036364,2.114286,2.10625,1.85,1.825,1.88125,1.0,0.980357,1.6375,1.7,0.995652,1.5625,1.885,1.775,1.075,0.966667,1.375,2.033333,2.10625,2.1625,2.1,2.085294,2.0,1.705,1.857143]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M11] rank=11 service=emailservice metric=container-memory-usage-bytes baseline=43976482.133333 peak=44105728.0 signed_z=36.712 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:43974656,0,0,0,0,4096,0,-2048,-2048,0,0,0,0,0,4096,0,-4096,-4096,4096,0,4096,0,0,4096,-8192,0,0,4096,0,-8192,0,0,0,4096,0,4096,0,-2048,-2048,0,0,0,0,4096,0,0,0,0,-4096,0,4096,-4096,-4096,135168,-126976,-4096,0,0,0,6144,-6144,2048,2048,-8192
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M12] rank=12 service=emailservice metric=container-memory-working-set-bytes baseline=43902754.133333 peak=44032000.0 signed_z=36.712 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:43900928,0,0,0,0,4096,0,-2048,-2048,0,0,0,0,0,4096,0,-4096,-4096,4096,0,4096,0,0,4096,-8192,0,0,4096,0,-8192,0,0,0,4096,0,4096,0,-2048,-2048,0,0,0,0,4096,0,0,0,0,-4096,0,4096,-4096,-4096,135168,-126976,-4096,0,0,0,6144,-6144,2048,2048,-8192
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[714.0,1440.0]

=== LOG SUMMARY ===
{"entries":[{"change_pct":-33.3,"n_during":10,"n_pre":15,"service":"redis"},{"change_pct":-13.3,"n_during":4710,"n_pre":5430,"service":"adservice"},{"change_pct":-13.0,"n_during":28185,"n_pre":32414,"service":"frontend"},{"change_pct":-12.2,"n_during":5915,"n_pre":6736,"service":"recommendationservice"},{"change_pct":-12.0,"n_during":8178,"n_pre":9290,"service":"cartservice"},{"change_pct":-11.6,"n_during":4796,"n_pre":5428,"service":"shippingservice"},{"change_pct":-10.8,"n_during":918,"n_pre":1029,"service":"checkoutservice"},{"change_pct":-10.8,"n_during":306,"n_pre":343,"service":"emailservice"}],"mode":"volume","omitted_services":1,"service_count":9}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":1054.5,"error_pct":0.0,"p95_during_ms":440.7328999999999,"p95_pre_ms":38.176,"service":"checkoutservice","spans":8924},{"delta_pct":961.7,"error_pct":0.0,"p95_during_ms":440.9511,"p95_pre_ms":41.533449999999995,"service":"frontend","spans":196642},{"delta_pct":8.7,"error_pct":0.0,"p95_during_ms":0.025,"p95_pre_ms":0.023,"service":"productcatalogservice","spans":97450},{"delta_pct":7.3,"error_pct":0.0,"p95_during_ms":0.4445,"p95_pre_ms":0.41440000000000016,"service":"emailservice","spans":1225},{"delta_pct":5.3,"error_pct":0.0,"p95_during_ms":0.3445499999999999,"p95_pre_ms":0.32719999999999994,"service":"paymentservice","spans":937},{"delta_pct":1.2,"error_pct":0.0,"p95_during_ms":4.461049999999999,"p95_pre_ms":4.4091499999999995,"service":"recommendationservice","spans":25878},{"delta_pct":0.0,"error_pct":0.0,"p95_during_ms":0.175,"p95_pre_ms":0.175,"service":"currencyservice","spans":54859}],"omitted_services":0,"service_count":7}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=3 omitted_edges=1
[{"evidence_source":"trace","onset_rel_s":735.0,"rank":1,"service":"checkoutservice","severity_z":159.503},{"evidence_source":"trace","onset_rel_s":735.0,"rank":2,"service":"frontend","severity_z":96.571},{"evidence_source":"metric","onset_rel_s":769.8,"rank":3,"service":"currencyservice","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":856.8,"rank":4,"service":"adservice","severity_z":22.51},{"evidence_source":"metric","onset_rel_s":982.2,"rank":5,"service":"redis","severity_z":19.26},{"evidence_source":"metric","onset_rel_s":1234.8,"rank":6,"service":"emailservice","severity_z":44.32},{"evidence_source":"metric","onset_rel_s":1351.2,"rank":7,"service":"shippingservice","severity_z":18.204},{"evidence_source":"none","onset_rel_s":null,"rank":8,"service":"paymentservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":9,"service":"gke-gke-cluster-default-pool-2e1807ce-xte3","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":10,"service":"gke-gke-cluster-default-pool-2e1807ce-w819","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":11,"service":"frontend-external","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":12,"service":"loadgenerator","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":13,"service":"cartservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":14,"service":"gke-gke-cluster-default-pool-2e1807ce-cx8g","severity_z":0.0}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"currencyservice","caller":"checkoutservice"},{"callee":"emailservice","caller":"checkoutservice"},{"callee":"paymentservice","caller":"checkoutservice"},{"callee":"checkoutservice","caller":"frontend"},{"callee":"currencyservice","caller":"frontend"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

{"confidence":"high","reason":"Rank currencyservice first because currencyservice has direct istio-latency-50 evidence (signed-z 999, persistence 31 bins); although checkoutservice is salient, the caller path checkoutservice -> currencyservice means a disturbance in the callee can propagate back toward that caller-side symptom.","services":["currencyservice","checkoutservice"]}

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
opaque_id: INC-AFCEA365A4AE
observation_window={"duration_rel_s":1440.0,"source_metric_rows":1441}
selection_summary={"candidate_count":17,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":268,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["adservice","cartservice","checkoutservice","currencyservice","emailservice","frontend","frontend-external","gke-gke-cluster-default-pool-2e1807ce-2969","gke-gke-cluster-default-pool-2e1807ce-957d","gke-gke-cluster-default-pool-2e1807ce-s8hw","gke-gke-cluster-default-pool-2e1807ce-xd9m","loadgenerator","paymentservice","productcatalogservice","recommendationservice","redis","shippingservice"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[11.25,33.75,56.25,78.75,101.25,123.75,146.25,168.75,191.25,213.75,236.25,258.75,281.25,303.75,326.25,348.75,371.25,393.75,416.25,438.75,461.25,483.75,506.25,528.75,551.25,573.75,596.25,618.75,641.25,663.75,686.25,708.75,731.25,753.75,776.25,798.75,821.25,843.75,866.25,888.75,911.25,933.75,956.25,978.75,1001.25,1023.75,1046.25,1068.75,1091.25,1113.75,1136.25,1158.75,1181.25,1203.75,1226.25,1248.75,1271.25,1293.75,1316.25,1338.75,1361.25,1383.75,1406.25,1428.75]
[M1] rank=1 service=productcatalogservice metric=container-memory-mapped-file baseline=0.0 peak=2207744.0 signed_z=999.0 onset_bin=32 onset_rel_s=731.25 persistence_bins=32
values_compact=rle:0*32,2207744*32
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M2] rank=2 service=productcatalogservice metric=istio-latency-90 baseline=0.004332 peak=0.049906 signed_z=999.0 onset_bin=32 onset_rel_s=731.25 persistence_bins=32
values_compact=raw:[0.004419,0.004363,0.004346,0.004343,0.004358,0.00437,0.004326,0.004324,0.004331,0.00432,0.004322,0.004312,0.004315,0.004327,0.00431,0.00431,0.004319,0.004315,0.004328,0.004333,0.004331,0.00434,0.004341,0.004335,0.004346,0.004339,0.004306,0.004292,0.004301,0.004324,0.004335,0.004345,0.004475,0.01517,0.044271,0.045543,0.045931,0.04555,0.043881,0.045002,0.046383,0.045084,0.044347,0.045737,0.046769,0.04851,0.049703,0.04702,0.045102,0.046194,0.047802,0.046705,0.044696,0.044948,0.046304,0.046659,0.046783,0.04667,0.046067,0.045897,0.047421,0.047916,0.04682,0.045489]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M3] rank=3 service=productcatalogservice metric=istio-latency-95 baseline=0.004671 peak=0.074855 signed_z=999.0 onset_bin=32 onset_rel_s=731.25 persistence_bins=32
values_compact=delta:0.004712,-0.000029,-0.000006,-0.000001,0.00001,0.000008,-0.000025,-0.000003,0.000002,-0.000006,0.000004,-0.000005,0,0.000005,-0.000007,0,0.000001,0,0.000007,0.000002,-0.000001,0.000005,0.000003,-0.000003,0.000013,0,-0.000025,-0.000011,0.000001,0.000013,0.000008,0.000009,0.00014,0.035812,0.019969,0.003462,0.000522,-0.000874,-0.007275,0.005132,0.005977,-0.004363,-0.005485,0.005998,0.004283,0.00435,0.0022,-0.005715,-0.006917,0.004538,0.004631,-0.002821,-0.006815,0.00094,0.003971,0.001394,0.000225,-0.000743,-0.001367,-0.000558,0.004003,0.001292,-0.002522,-0.003443
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M4] rank=4 service=productcatalogservice metric=istio-latency-99 baseline=0.004942 peak=0.094971 signed_z=999.0 onset_bin=32 onset_rel_s=731.25 persistence_bins=32
values_compact=raw:[0.004947,0.004939,0.004942,0.004943,0.004949,0.004953,0.004944,0.004941,0.004938,0.004935,0.004941,0.00494,0.004937,0.004938,0.004938,0.004939,0.004934,0.004935,0.004938,0.004937,0.004938,0.004939,0.004944,0.004942,0.004958,0.004963,0.004945,0.004937,0.004931,0.004938,0.004941,0.00495,0.044604,0.07871,0.09212,0.092813,0.092917,0.092742,0.091287,0.092314,0.093509,0.092637,0.09154,0.092739,0.093596,0.094466,0.094906,0.093763,0.092379,0.093287,0.094213,0.093649,0.092286,0.092474,0.093268,0.093547,0.093592,0.093443,0.09317,0.093058,0.093859,0.094117,0.093613,0.092924]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M5] rank=5 service=gke-gke-cluster-default-pool-2e1807ce-s8hw metric=node-memory-active-bytes baseline=6552.588642 peak=22571053.511111 signed_z=999.0 onset_bin=47 onset_rel_s=1068.75 persistence_bins=2
values_compact=delta:5188.266667,91.022222,910.222222,1001.244445,455.111111,455.111111,-1001.244445,-1319.822222,136.533333,364.088889,182.044445,637.155555,-182.044444,-455.111111,91.022222,-318.577778,-500.622222,546.133333,546.133334,227.555555,864.711111,-409.6,-682.666666,-1547.377778,546.133333,955.733334,-1319.822223,182.044445,1001.244444,273.066667,0,773.688889,-227.555556,-273.066666,-182.044445,91.022222,-182.044444,-1820.444445,-1001.244444,2139.022222,318.577778,-455.111111,364.088889,-227.555556,-227.555555,-864.711111,864.711111,22564545.422222,318.577778,-22563271.111111,-1592.888889,-1319.822223,2230.044445,546.133333,-819.2,273.066667,546.133333,-500.622222,-1774.933333,637.155555,1001.244445,-1365.333334,-637.155555,1547.377778
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M6] rank=6 service=recommendationservice metric=istio-latency-90 baseline=0.00955 peak=0.073237 signed_z=508.944 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=raw:[0.009392,0.009494,0.009527,0.009539,0.009784,0.009848,0.009662,0.009691,0.009616,0.009468,0.009477,0.009489,0.009453,0.009456,0.009424,0.009441,0.009448,0.009487,0.009604,0.009583,0.009469,0.009441,0.009517,0.009531,0.009685,0.009688,0.00947,0.009456,0.009429,0.009508,0.009681,0.009816,0.009868,0.046029,0.058838,0.056383,0.058925,0.06266,0.049455,0.048256,0.04923,0.049468,0.049726,0.06112,0.058278,0.062895,0.073105,0.067581,0.0618,0.061994,0.060053,0.059468,0.0502,0.049503,0.054943,0.059427,0.064868,0.058434,0.058622,0.061308,0.062362,0.062455,0.059764,0.056302]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M7] rank=7 service=adservice metric=istio-latency-99 baseline=0.004971 peak=0.0077 signed_z=254.148 onset_bin=45 onset_rel_s=1023.75 persistence_bins=3
values_compact=delta:0.00496,0,0.000006,0.000007,0.000025,0,-0.000025,-0.000007,0.000012,0.000007,-0.000019,-0.000006,0,0,0,0.000006,0.000012,-0.000006,0.000006,0,-0.000012,0.000012,0.000001,-0.000013,0.000006,0,-0.000006,0,-0.000006,0,0.000012,0.000013,0.000012,-0.000006,-0.000018,-0.000007,0.000031,0,-0.000013,0.000928,-0.000928,-0.000018,0.000031,0.001459,-0.001471,0.001121,0.000699,-0.001833,-0.000012,0.000018,0.000001,-0.000013,0.000025,-0.000007,0.000007,0.00058,-0.000579,-0.000014,0.00002,0.000001,-0.000007,0.000006,-0.00002,-0.000006
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M8] rank=8 service=recommendationservice metric=istio-latency-50 baseline=0.007119 peak=0.033241 signed_z=162.531 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=raw:[0.006589,0.006899,0.00707,0.007063,0.007149,0.007318,0.007232,0.007246,0.007228,0.007016,0.006995,0.007061,0.00703,0.006991,0.006946,0.007025,0.007124,0.007212,0.007192,0.007155,0.007147,0.007121,0.007162,0.00718,0.007228,0.007177,0.007115,0.007061,0.007057,0.007251,0.007383,0.007446,0.007404,0.008268,0.028812,0.031607,0.031066,0.027902,0.025997,0.027952,0.02834,0.027312,0.028177,0.029839,0.030371,0.029563,0.030368,0.03273,0.031496,0.028325,0.02912,0.030771,0.029675,0.028753,0.030297,0.029273,0.029594,0.029825,0.029256,0.031763,0.032884,0.031396,0.030693,0.029471]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M9] rank=9 service=productcatalogservice metric=container-memory-cache baseline=0.0 peak=2207744.0 signed_z=125.32 onset_bin=32 onset_rel_s=731.25 persistence_bins=32
values_compact=rle:0*32,2207744*32
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M10] rank=10 service=productcatalogservice metric=container-cpu-user-seconds-total baseline=1.840084 peak=19.590027 signed_z=57.303 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=delta:0.698228,0.862937,0.374833,0.022746,-0.000872,-0.005854,-0.366752,0.274256,-0.107937,0.273902,-0.002268,-0.143974,0.067214,-0.013271,0.017643,0.002357,-0.025283,-0.065034,0,0.178992,-0.034072,0.069608,-0.377922,0.256521,0.179574,-0.011481,-0.108696,-0.054133,-0.061594,-0.006981,0.024256,0.038554,0.765948,8.997255,7.869272,-0.028695,-0.030485,-0.034616,-0.034532,0.036824,0.01396,0.007213,0.01102,-0.053619,-0.02527,-0.00494,-0.037875,-2.455628,2.413403,0.009707,-0.025808,-0.072205,0.049284,0.1332,0.070915,-0.016366,-0.068843,-0.057518,0.012511,-0.011409,-0.010988,-0.064673,-0.000153,0.041234
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,20,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M11] rank=11 service=recommendationservice metric=istio-latency-95 baseline=0.01035 peak=0.086619 signed_z=51.372 onset_bin=32 onset_rel_s=731.25 persistence_bins=32
values_compact=raw:[0.009743,0.009818,0.009834,0.00985,0.01434,0.015673,0.009965,0.009996,0.009915,0.009775,0.009787,0.009792,0.009756,0.009764,0.009734,0.00974,0.009736,0.009772,0.009903,0.009886,0.00976,0.009731,0.009811,0.009825,0.009999,0.01015,0.009764,0.009755,0.009719,0.00979,0.009969,0.014095,0.020103,0.062364,0.079419,0.078191,0.080806,0.083989,0.074154,0.062176,0.070978,0.072958,0.073697,0.08056,0.079139,0.081447,0.086552,0.08379,0.0809,0.080997,0.080682,0.080798,0.075767,0.072353,0.077471,0.079714,0.082434,0.079217,0.079311,0.080654,0.081181,0.081228,0.079882,0.078151]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M12] rank=12 service=productcatalogservice metric=container-cpu-usage-seconds-total baseline=2.655822 peak=20.019678 signed_z=39.032 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=delta:0.982899,1.326361,0.531948,-0.00316,-0.05656,-0.010554,-0.520612,0.40385,-0.131617,0.401117,-0.031914,-0.170461,0.099094,0.007876,0.007294,0.000301,0.05154,-0.053955,0,0.09643,-0.042276,0.091816,-0.50455,0.430954,0.113491,-0.044784,-0.162507,-0.078647,-0.038215,0.017539,0.051707,0.070227,0.760967,8.834821,7.573838,0.003059,-0.009885,-0.012192,-0.000331,0.01233,-0.006817,-0.010431,0.001284,-0.005254,0.028006,-0.013269,0.021614,-2.512405,2.473401,0.019598,0.005303,-0.037207,0.026644,0.001917,-0.016108,0.021962,-0.007709,0.006952,-0.014765,-0.008945,0.029795,-0.010587,-0.001513,0.003369
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,20,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[700.0,1440.0]

=== LOG SUMMARY ===
{"entries":[{"change_pct":50.0,"n_during":15,"n_pre":10,"service":"redis"},{"change_pct":17.8,"n_during":1039,"n_pre":882,"service":"checkoutservice"},{"change_pct":17.7,"n_during":346,"n_pre":294,"service":"emailservice"},{"change_pct":17.7,"n_during":692,"n_pre":588,"service":"paymentservice"},{"change_pct":8.6,"n_during":5388,"n_pre":4962,"service":"shippingservice"},{"change_pct":5.4,"n_during":6609,"n_pre":6272,"service":"recommendationservice"},{"change_pct":5.3,"n_during":9101,"n_pre":8642,"service":"cartservice"},{"change_pct":4.2,"n_during":31341,"n_pre":30075,"service":"frontend"}],"mode":"volume","omitted_services":2,"service_count":10}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":984.2,"error_pct":0.0,"p95_during_ms":49.448699999999995,"p95_pre_ms":4.5608499999999985,"service":"recommendationservice","spans":26338},{"delta_pct":26.3,"error_pct":0.0,"p95_during_ms":0.024,"p95_pre_ms":0.019,"service":"productcatalogservice","spans":99444},{"delta_pct":-26.2,"error_pct":0.0,"p95_during_ms":0.5743499999999986,"p95_pre_ms":0.7786999999999993,"service":"paymentservice","spans":928},{"delta_pct":20.3,"error_pct":0.0,"p95_during_ms":230.8835,"p95_pre_ms":191.9685999999998,"service":"frontend","spans":200295},{"delta_pct":3.8,"error_pct":0.0,"p95_during_ms":0.40095,"p95_pre_ms":0.3864000000000001,"service":"emailservice","spans":1216},{"delta_pct":1.6,"error_pct":0.0,"p95_during_ms":0.192,"p95_pre_ms":0.189,"service":"currencyservice","spans":55953},{"delta_pct":-1.5,"error_pct":0.0,"p95_during_ms":209.47054999999997,"p95_pre_ms":212.72674999999992,"service":"checkoutservice","spans":9092}],"omitted_services":0,"service_count":7}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=3 omitted_edges=0
[{"evidence_source":"trace","onset_rel_s":735.0,"rank":1,"service":"recommendationservice","severity_z":120.127},{"evidence_source":"trace","onset_rel_s":855.0,"rank":2,"service":"productcatalogservice","severity_z":4.351},{"evidence_source":"metric","onset_rel_s":858.0,"rank":3,"service":"adservice","severity_z":254.148},{"evidence_source":"metric","onset_rel_s":1054.2,"rank":4,"service":"gke-gke-cluster-default-pool-2e1807ce-s8hw","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1285.2,"rank":5,"service":"emailservice","severity_z":10.455},{"evidence_source":"none","onset_rel_s":null,"rank":6,"service":"currencyservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":7,"service":"paymentservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":8,"service":"frontend","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":9,"service":"gke-gke-cluster-default-pool-2e1807ce-xd9m","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":10,"service":"frontend-external","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":11,"service":"shippingservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":12,"service":"cartservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":13,"service":"redis","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":14,"service":"gke-gke-cluster-default-pool-2e1807ce","severity_z":0.0}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"currencyservice","caller":"frontend"},{"callee":"productcatalogservice","caller":"frontend"},{"callee":"recommendationservice","caller":"frontend"},{"callee":"productcatalogservice","caller":"recommendationservice"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

{"confidence":"high","reason":"Rank productcatalogservice first because productcatalogservice has direct container-memory-mapped-file evidence (signed-z 999, persistence 32 bins); although recommendationservice is salient, the caller path recommendationservice -> productcatalogservice means a disturbance in the callee can propagate back toward that caller-side symptom.","services":["productcatalogservice","recommendationservice"]}

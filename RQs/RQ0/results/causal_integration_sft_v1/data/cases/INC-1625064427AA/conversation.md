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
opaque_id: INC-1625064427AA
observation_window={"duration_rel_s":1440.0,"source_metric_rows":1441}
selection_summary={"candidate_count":17,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":269,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["adservice","cartservice","checkoutservice","currencyservice","emailservice","frontend","frontend-external","gke-gke-cluster-default-pool-2e1807ce-0e4z","gke-gke-cluster-default-pool-2e1807ce-cx8g","gke-gke-cluster-default-pool-2e1807ce-w819","gke-gke-cluster-default-pool-2e1807ce-xte3","loadgenerator","paymentservice","productcatalogservice","recommendationservice","redis","shippingservice"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[11.25,33.75,56.25,78.75,101.25,123.75,146.25,168.75,191.25,213.75,236.25,258.75,281.25,303.75,326.25,348.75,371.25,393.75,416.25,438.75,461.25,483.75,506.25,528.75,551.25,573.75,596.25,618.75,641.25,663.75,686.25,708.75,731.25,753.75,776.25,798.75,821.25,843.75,866.25,888.75,911.25,933.75,956.25,978.75,1001.25,1023.75,1046.25,1068.75,1091.25,1113.75,1136.25,1158.75,1181.25,1203.75,1226.25,1248.75,1271.25,1293.75,1316.25,1338.75,1361.25,1383.75,1406.25,1428.75]
[M1] rank=1 service=currencyservice metric=container-memory-mapped-file baseline=0.0 peak=2211840.0 signed_z=999.0 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=rle:0*33,2211840*31
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M2] rank=2 service=frontend-external metric=istio-error-total baseline=0.0 peak=0.133 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=rle:0*64
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M3] rank=3 service=cartservice metric=istio-latency-90 baseline=0.004792 peak=0.1195 signed_z=999.0 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=raw:[0.0049,0.0048,0.004735,0.004731,0.004745,0.00477,0.004794,0.004786,0.004756,0.00481,0.004815,0.0048,0.00478,0.004718,0.004834,0.004882,0.004847,0.004817,0.004769,0.004701,0.004753,0.004825,0.004787,0.00475,0.004876,0.004947,0.004804,0.004801,0.004785,0.004717,0.004755,0.004746,0.004794,0.005449,0.006592,0.006768,0.005941,0.005393,0.006339,0.007118,0.007324,0.00781,0.007081,0.006843,0.007476,0.006449,0.005927,0.006556,0.006772,0.006661,0.005589,0.00689,0.00701,0.007224,0.009856,0.008917,0.006021,0.006595,0.008692,0.085833,0.008525,0.005759,0.006539,0.006639]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M4] rank=4 service=gke-gke-cluster-default-pool-2e1807ce-w819 metric=node-memory-active-bytes baseline=2517.142061 peak=22323200.0 signed_z=999.0 onset_bin=41 onset_rel_s=933.75 persistence_bins=2
values_compact=delta:1729.422222,91.022222,546.133334,364.088889,273.066666,-364.088889,-1001.244444,273.066667,455.111111,-364.088889,819.0119,364.276989,-1092.12709,-91.161799,819.2,364.088889,-1092.266667,91.022222,546.133334,91.022222,637.155555,-728.177777,91.022222,-91.022222,-273.066667,637.155556,-455.111112,-182.044444,-182.044444,-273.066667,637.155555,182.044445,637.155555,728.177778,-910.222222,-455.111111,-182.044445,-182.044444,273.066667,-182.044445,-91.022222,22320742.4,-91.022222,-22320469.333334,273.066667,-273.066667,-546.133333,182.044445,364.088888,91.022223,0,-182.044445,182.044445,-91.022223,364.088889,-91.022222,-91.022222,364.088889,-637.155556,-273.066666,546.133333,364.088889,182.044444,-182.044444
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M5] rank=5 service=currencyservice metric=container-memory-usage-bytes baseline=44232027.022222 peak=268439552.0 signed_z=580.514 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=delta:44781568,-483328,184320,344064,-1212416,583680,292864,-860160,278528,77824,286720,-462848,331776,860160,-966656,139264,-380928,303104,630784,-573440,172032,835584,-1081344,208896,126976,-151552,733184,-1089536,106496,327680,-303104,49152,446464,223899648,-147456,0,36864,-49152,20480,139264,-98304,-106496,4096,145408,-63670272,-1536000,65212416,-4096,-131072,73728,16384,69632,-45056,-98304,172032,-139264,73728,-24576,-128622592,11677696,117026816,-16384,-188416,200704
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M6] rank=6 service=currencyservice metric=istio-latency-50 baseline=0.004055 peak=0.071339 signed_z=509.907 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=raw:[0.003889,0.003885,0.004069,0.004177,0.004088,0.004035,0.004062,0.004088,0.004115,0.004117,0.004065,0.004053,0.004082,0.004119,0.00431,0.004387,0.004204,0.004144,0.004082,0.003989,0.004024,0.004141,0.004148,0.004029,0.004054,0.004006,0.003824,0.00391,0.004012,0.003888,0.00385,0.003921,0.004023,0.017446,0.069778,0.068205,0.062875,0.061524,0.06292,0.062822,0.058843,0.061089,0.061781,0.061529,0.063023,0.062451,0.063989,0.062322,0.060634,0.063109,0.064892,0.063099,0.062883,0.062372,0.060669,0.063213,0.066132,0.063256,0.060738,0.061974,0.063017,0.060135,0.058718,0.0615]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M7] rank=7 service=currencyservice metric=container-memory-cache baseline=0.0 peak=221425664.0 signed_z=363.853 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,220938240,-5148672,0,696320,4591616,-4562944,4694016,-4444160,4087808,-4800512,2686976,-62976000,-563200,62388224,-962560,798720,-1687552,-4096,741376,-753664,4894720,-5521408,36864,1163264,118784,-123637760,11202560,112439296,-593920,1032192,4300800
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M8] rank=8 service=currencyservice metric=istio-latency-99 baseline=0.094996 peak=0.395303 signed_z=337.772 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=raw:[0.093239,0.093568,0.094916,0.096317,0.09648,0.095212,0.095488,0.095606,0.095931,0.095806,0.094864,0.094858,0.09491,0.094994,0.096268,0.096152,0.096101,0.095979,0.094682,0.094035,0.094141,0.094949,0.094903,0.09482,0.095179,0.094304,0.093523,0.094106,0.094577,0.094512,0.094992,0.094581,0.095562,0.244242,0.372235,0.378598,0.24885,0.235913,0.359476,0.360121,0.235852,0.24422,0.245562,0.239625,0.241885,0.24221,0.245265,0.242352,0.229636,0.236183,0.242368,0.240119,0.275329,0.248207,0.239758,0.249874,0.306081,0.2473,0.378009,0.377105,0.245296,0.239038,0.234712,0.241571]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M9] rank=9 service=recommendationservice metric=istio-latency-95 baseline=0.009829 peak=0.020036 signed_z=174.652 onset_bin=33 onset_rel_s=753.75 persistence_bins=23
values_compact=raw:[0.009819,0.009811,0.009807,0.009806,0.009831,0.009878,0.009826,0.009801,0.009823,0.009791,0.009776,0.009851,0.009839,0.009837,0.009905,0.009981,0.00991,0.009795,0.009789,0.009763,0.009756,0.009797,0.009808,0.009796,0.009919,0.009984,0.009866,0.009762,0.009789,0.009834,0.00981,0.009764,0.009795,0.011484,0.013764,0.009982,0.009946,0.009846,0.009868,0.012136,0.012674,0.013651,0.01082,0.00991,0.012781,0.013015,0.009944,0.009911,0.009944,0.014158,0.011986,0.012233,0.017105,0.018178,0.018311,0.017705,0.014339,0.013317,0.017697,0.020036,0.017775,0.010663,0.013,0.013087]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M10] rank=10 service=checkoutservice metric=istio-latency-90 baseline=0.226333 peak=1.3 signed_z=167.769 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=raw:[0.21625,0.218235,0.2185,0.210625,0.217,0.227241,0.235,0.237143,0.226429,0.230781,0.2335,0.234348,0.230263,0.23,0.236184,0.230625,0.2215,0.222812,0.226923,0.231379,0.2325,0.231538,0.2275,0.225294,0.226136,0.2275,0.22525,0.226522,0.225526,0.222308,0.223409,0.219375,0.229474,0.428571,0.811111,0.8625,0.485714,0.46125,0.558333,0.65,0.75,0.9,0.525,0.5,0.497222,0.794444,0.861538,0.7625,0.481667,0.45625,0.633333,0.841667,0.859091,0.744444,0.8625,1.075,0.778571,0.566667,0.854545,0.876316,0.711111,0.468519,0.6,0.6875]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M11] rank=11 service=gke-gke-cluster-default-pool-2e1807ce-cx8g metric=node-disk-written-bytes-total baseline=2752305.669347 peak=72460515.555556 signed_z=134.09 onset_bin=32 onset_rel_s=731.25 persistence_bins=32
values_compact=delta:2527323.022222,-158924.8,471586.133334,258503.111111,-555690.666667,-127886.222222,93297.777778,85469.866666,128796.444445,-192420.977778,-235747.555556,306744.888889,347158.755556,1087624.533333,-59164.444444,-1268758.755556,-93570.844444,92933.688889,-20571.022223,11832.888889,-238023.111111,1336388.266667,151187.911111,-1600352.711111,62532.266666,57435.022223,-9011.2,222913.422222,12470.044444,-231287.466666,-2366.577778,42780.444444,16769768.44706,17212741.064051,20770176.886412,6623416.002477,-3382175.56918,-7668377.319709,11416735.288889,7440747.396186,-10027963.04063,-5426868.510803,6139026.37747,2424285.866666,-6957247.363073,-2792597.97026,14510572.115756,2905073.750911,-16148525.511112,-3025309.038311,13532106.177798,-241721.275749,-13322875.571693,4650581.321954,13503745.250414,-4190699.308857,-13642843.979536,5595842.379536,8022243.555556,-8420711.304367,-2055533.174628,8696208.435595,-4041558.676478,-8471351.769011
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M12] rank=12 service=checkoutservice metric=istio-latency-95 baseline=0.243759 peak=1.9 signed_z=100.801 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=raw:[0.233125,0.234118,0.23425,0.230312,0.2335,0.238621,0.249022,0.3,0.240893,0.24525,0.24675,0.248696,0.2475,0.242273,0.247,0.246429,0.2485,0.241094,0.241346,0.245862,0.24875,0.246111,0.23875,0.237647,0.238068,0.23875,0.237625,0.238261,0.237763,0.236154,0.236705,0.234687,0.247632,0.5,0.905556,0.990625,1.0,0.493125,0.779167,0.8875,1.375,1.55,0.991667,0.75,0.7375,0.897222,0.930769,0.88125,0.658333,0.488542,0.9,1.075,0.952273,0.872222,1.65625,1.7875,0.889286,0.783333,0.927273,0.938158,0.855556,0.488889,0.8,0.84375]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[715.0,1440.0]

=== LOG SUMMARY ===
{"entries":[{"change_pct":50.0,"n_during":15,"n_pre":10,"service":"redis"},{"change_pct":-5.6,"n_during":966,"n_pre":1023,"service":"checkoutservice"},{"change_pct":-5.6,"n_during":322,"n_pre":341,"service":"emailservice"},{"change_pct":-5.6,"n_during":644,"n_pre":682,"service":"paymentservice"},{"change_pct":-4.4,"n_during":5132,"n_pre":5370,"service":"shippingservice"},{"change_pct":-3.6,"n_during":6556,"n_pre":6799,"service":"recommendationservice"},{"change_pct":-3.2,"n_during":9000,"n_pre":9295,"service":"cartservice"},{"change_pct":-2.0,"n_during":5302,"n_pre":5410,"service":"adservice"}],"mode":"volume","omitted_services":2,"service_count":10}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":192.7,"error_pct":0.0,"p95_during_ms":197.813,"p95_pre_ms":67.58709999999994,"service":"frontend","spans":205476},{"delta_pct":160.2,"error_pct":0.0,"p95_during_ms":208.83350000000002,"p95_pre_ms":80.24539999999986,"service":"checkoutservice","spans":9260},{"delta_pct":43.8,"error_pct":0.0,"p95_during_ms":0.36094999999999705,"p95_pre_ms":0.251,"service":"currencyservice","spans":56397},{"delta_pct":15.0,"error_pct":0.0,"p95_during_ms":5.234849999999997,"p95_pre_ms":4.5528499999999985,"service":"recommendationservice","spans":27286},{"delta_pct":-5.1,"error_pct":0.0,"p95_during_ms":0.37324999999999997,"p95_pre_ms":0.39339999999999875,"service":"paymentservice","spans":951},{"delta_pct":-2.3,"error_pct":0.0,"p95_during_ms":0.43679999999999974,"p95_pre_ms":0.44709999999999983,"service":"emailservice","spans":1239},{"delta_pct":-1.3,"error_pct":0.0,"p95_during_ms":0.02369999999999709,"p95_pre_ms":0.024,"service":"productcatalogservice","spans":102715}],"omitted_services":0,"service_count":7}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=3 omitted_edges=1
[{"evidence_source":"trace","onset_rel_s":735.0,"rank":1,"service":"checkoutservice","severity_z":21.203},{"evidence_source":"trace","onset_rel_s":735.0,"rank":2,"service":"frontend","severity_z":32.542},{"evidence_source":"metric","onset_rel_s":759.0,"rank":3,"service":"gke-gke-cluster-default-pool-2e1807ce-cx8g","severity_z":134.09},{"evidence_source":"trace","onset_rel_s":765.0,"rank":4,"service":"currencyservice","severity_z":13.354},{"evidence_source":"metric","onset_rel_s":790.2,"rank":5,"service":"shippingservice","severity_z":84.728},{"evidence_source":"metric","onset_rel_s":873.0,"rank":6,"service":"frontend-external","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":921.0,"rank":7,"service":"gke-gke-cluster-default-pool-2e1807ce-w819","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1210.2,"rank":8,"service":"emailservice","severity_z":34.729},{"evidence_source":"metric","onset_rel_s":1327.2,"rank":9,"service":"cartservice","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1402.2,"rank":10,"service":"adservice","severity_z":37.569},{"evidence_source":"metric","onset_rel_s":1402.2,"rank":11,"service":"redis","severity_z":16.734},{"evidence_source":"trace","onset_rel_s":1425.0,"rank":12,"service":"recommendationservice","severity_z":4.009},{"evidence_source":"none","onset_rel_s":null,"rank":13,"service":"paymentservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":14,"service":"gke-gke-cluster-default-pool-2e1807ce-0e4z","severity_z":0.0}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"currencyservice","caller":"checkoutservice"},{"callee":"emailservice","caller":"checkoutservice"},{"callee":"paymentservice","caller":"checkoutservice"},{"callee":"checkoutservice","caller":"frontend"},{"callee":"currencyservice","caller":"frontend"},{"callee":"recommendationservice","caller":"frontend"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

{"confidence":"high","reason":"Rank currencyservice first because currencyservice has direct container-memory-mapped-file evidence (signed-z 999, persistence 31 bins); although checkoutservice is salient, the caller path checkoutservice -> currencyservice means a disturbance in the callee can propagate back toward that caller-side symptom.","services":["currencyservice","checkoutservice"]}

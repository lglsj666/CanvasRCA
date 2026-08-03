# Causal SFT v2 base rollout — INC-FC88448A9C8E

## System

You are an expert Site Reliability Engineer performing Root Cause Analysis (RCA) for a microservice application deployed on a Kubernetes cluster. A fault has occurred in the system. Your task is to identify the root cause of the incident.

Root causes can occur at three levels:
- Pod level: a specific container replica (e.g., "cartservice-0")
- Service level: a microservice type (e.g., "paymentservice") — predict any pod of that service
- Node level: an infrastructure host (e.g., "node-6") — nodes appear as isolated entities with system metrics (CPU, memory, network, disk) but no application logs or traces

The system consists of multiple services communicating over HTTP/gRPC, running on shared infrastructure nodes. A fault in one component (pod, service, or node) can propagate to dependent components, causing them to appear degraded even though they are not the root cause.

Node-level faults (e.g., host memory exhaustion, CPU saturation, disk I/O) often manifest as correlated anomalies across multiple pods. If several unrelated pods show simultaneous degradation and a node shows critical system-level metrics, the node is likely the root cause.

Focus on distinguishing the ORIGIN of the fault from its SYMPTOMS in downstream or co-located components.

## User

[image: RQs/RQ0/results/causal_integration_sft_v1/data/cases/INC-FC88448A9C8E/dashboard.png]

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
opaque_id: INC-FC88448A9C8E
observation_window={"duration_rel_s":1440.0,"source_metric_rows":1441}
selection_summary={"candidate_count":17,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":265,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["adservice","cartservice","checkoutservice","currencyservice","emailservice","frontend","frontend-external","gke-gke-cluster-default-pool-2e1807ce-0e4z","gke-gke-cluster-default-pool-2e1807ce-cx8g","gke-gke-cluster-default-pool-2e1807ce-w819","gke-gke-cluster-default-pool-2e1807ce-xte3","loadgenerator","paymentservice","productcatalogservice","recommendationservice","redis","shippingservice"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[11.25,33.75,56.25,78.75,101.25,123.75,146.25,168.75,191.25,213.75,236.25,258.75,281.25,303.75,326.25,348.75,371.25,393.75,416.25,438.75,461.25,483.75,506.25,528.75,551.25,573.75,596.25,618.75,641.25,663.75,686.25,708.75,731.25,753.75,776.25,798.75,821.25,843.75,866.25,888.75,911.25,933.75,956.25,978.75,1001.25,1023.75,1046.25,1068.75,1091.25,1113.75,1136.25,1158.75,1181.25,1203.75,1226.25,1248.75,1271.25,1293.75,1316.25,1338.75,1361.25,1383.75,1406.25,1428.75]
[M1] rank=1 service=currencyservice metric=container-memory-mapped-file baseline=0.0 peak=2215936.0 signed_z=999.0 onset_bin=32 onset_rel_s=731.25 persistence_bins=32
values_compact=rle:0*32,2215936*32
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M2] rank=2 service=gke-gke-cluster-default-pool-2e1807ce-w819 metric=node-memory-active-bytes baseline=2608.924445 peak=22284515.555556 signed_z=999.0 onset_bin=48 onset_rel_s=1091.25 persistence_bins=2
values_compact=delta:2639.644444,637.155556,-728.177778,-273.066666,273.066666,0,364.088889,-637.155555,-273.066667,910.222222,-0.194168,-545.939165,546.327527,363.894695,-455.111111,-819.2,273.066667,637.155555,-182.044444,273.066666,91.022223,-455.111112,-91.022222,91.022222,91.022223,-182.044445,-182.044444,-546.133334,-182.044444,728.177778,455.111111,455.111111,-91.022222,-91.022222,91.022222,91.022222,-637.155556,0,273.066667,-1183.288889,364.088889,1001.244445,-91.022223,-91.022222,-182.044444,-182.044445,637.155556,-91.022222,22281420.8,0,-22282422.044445,819.2,273.066667,-910.222222,273.066666,182.044445,-364.088889,-91.022222,455.111111,364.088889,-273.066667,-91.022222,-273.066667,-91.022222
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M3] rank=3 service=currencyservice metric=container-sockets baseline=4.0 peak=19.0 signed_z=789.474 onset_bin=32 onset_rel_s=731.25 persistence_bins=32
values_compact=rle:4*32,17*1,17.5*1,18*2,17*2,18*5,17*1,19*1,17*1,18*3,17*3,18*1,17*1,18*1,17*4,18*3,19*1,17*1
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M4] rank=4 service=currencyservice metric=istio-latency-99 baseline=0.095452 peak=0.447565 signed_z=506.11 onset_bin=32 onset_rel_s=731.25 persistence_bins=32
values_compact=raw:[0.09586,0.095812,0.096255,0.095452,0.095327,0.096076,0.095326,0.094115,0.094451,0.094832,0.094671,0.094631,0.095536,0.096278,0.095953,0.094815,0.095019,0.096025,0.095399,0.094721,0.095505,0.095583,0.096078,0.095008,0.094406,0.095749,0.095487,0.096846,0.096983,0.095722,0.095382,0.09508,0.098279,0.263857,0.357544,0.320156,0.249481,0.242413,0.241756,0.391948,0.410173,0.239964,0.21121,0.21998,0.229525,0.247146,0.441644,0.436673,0.233714,0.221271,0.246365,0.246327,0.224858,0.212862,0.210961,0.215328,0.214809,0.222526,0.236068,0.233121,0.247874,0.267,0.226197,0.206911]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M5] rank=5 service=currencyservice metric=istio-latency-50 baseline=0.004123 peak=0.073456 signed_z=454.631 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=raw:[0.004344,0.004267,0.004104,0.003991,0.004163,0.004351,0.00412,0.003893,0.00399,0.004027,0.003906,0.003949,0.004143,0.004372,0.004305,0.004068,0.004076,0.004127,0.00388,0.003944,0.00426,0.004233,0.004225,0.004028,0.003902,0.004135,0.004183,0.004318,0.004376,0.004171,0.004049,0.003997,0.004161,0.016953,0.070351,0.070126,0.069213,0.069606,0.069711,0.07323,0.06966,0.059046,0.057923,0.059016,0.059462,0.061739,0.066485,0.065476,0.059886,0.05743,0.057111,0.05495,0.050927,0.055584,0.060101,0.060301,0.058935,0.059659,0.062117,0.061446,0.060586,0.061318,0.060061,0.05705]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M6] rank=6 service=cartservice metric=istio-latency-95 baseline=0.00618 peak=0.55 signed_z=426.305 onset_bin=33 onset_rel_s=753.75 persistence_bins=5
values_compact=raw:[0.009407,0.008192,0.005935,0.00497,0.005212,0.008818,0.005878,0.004957,0.006,0.006036,0.004977,0.006367,0.006469,0.005997,0.006611,0.006668,0.005215,0.004955,0.004928,0.00494,0.006852,0.006293,0.004983,0.004992,0.004923,0.004961,0.00599,0.00705,0.007384,0.007583,0.007282,0.005718,0.00828,0.525862,0.482759,0.008207,0.008448,0.008373,0.008503,0.008508,0.008592,0.008388,0.008044,0.008104,0.008091,0.008136,0.016,0.023375,0.00832,0.008701,0.009618,0.009259,0.008242,0.008723,0.009083,0.00844,0.008318,0.008155,0.007937,0.007965,0.009465,0.01045,0.009821,0.009165]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M7] rank=7 service=cartservice metric=istio-latency-90 baseline=0.00494 peak=0.241 signed_z=420.055 onset_bin=33 onset_rel_s=753.75 persistence_bins=16
values_compact=raw:[0.007799,0.005495,0.004829,0.004761,0.004795,0.004893,0.004814,0.004749,0.004837,0.00484,0.004768,0.004854,0.004863,0.004835,0.004868,0.00485,0.004796,0.004746,0.004722,0.004733,0.004872,0.004839,0.004773,0.004782,0.004717,0.004753,0.004824,0.004881,0.004922,0.004911,0.004871,0.004814,0.004932,0.22,0.125,0.006132,0.006623,0.006673,0.00695,0.006876,0.006922,0.006537,0.005837,0.006026,0.006146,0.006197,0.008173,0.008061,0.006184,0.006672,0.007407,0.007117,0.006213,0.006742,0.006842,0.006305,0.006427,0.006156,0.005819,0.005768,0.007367,0.007954,0.007606,0.006534]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M8] rank=8 service=currencyservice metric=container-memory-cache baseline=0.0 peak=2244608.0 signed_z=408.267 onset_bin=32 onset_rel_s=731.25 persistence_bins=32
values_compact=rle:0*32,2244608*32
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M9] rank=9 service=recommendationservice metric=istio-latency-95 baseline=0.009832 peak=0.019639 signed_z=224.842 onset_bin=32 onset_rel_s=731.25 persistence_bins=22
values_compact=raw:[0.009916,0.009874,0.009795,0.009779,0.009805,0.009869,0.009863,0.009804,0.009774,0.009777,0.009763,0.009784,0.009797,0.009789,0.009854,0.009933,0.009863,0.009832,0.009863,0.009816,0.009919,0.009911,0.009819,0.00986,0.009818,0.009772,0.00982,0.009828,0.009825,0.009819,0.009843,0.009851,0.00999,0.018792,0.017674,0.011286,0.012908,0.009982,0.00991,0.009939,0.009948,0.009905,0.00991,0.009916,0.009893,0.0099,0.018039,0.018667,0.012571,0.012109,0.013818,0.014329,0.013375,0.011814,0.009969,0.009978,0.009943,0.009992,0.014709,0.013552,0.010348,0.010183,0.009994,0.009921]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M10] rank=10 service=recommendationservice metric=istio-latency-90 baseline=0.009572 peak=0.013332 signed_z=90.119 onset_bin=32 onset_rel_s=731.25 persistence_bins=22
values_compact=raw:[0.009655,0.009615,0.009537,0.009521,0.009546,0.009608,0.009602,0.009546,0.009517,0.009518,0.009507,0.009529,0.00954,0.009531,0.009594,0.009668,0.0096,0.009572,0.009604,0.009558,0.009654,0.009647,0.00956,0.009598,0.009556,0.009514,0.009561,0.009568,0.009566,0.00956,0.009583,0.009589,0.009719,0.0115,0.009975,0.009756,0.009793,0.009714,0.009646,0.009672,0.009682,0.00964,0.009646,0.009652,0.009631,0.009637,0.009962,0.01025,0.009784,0.009772,0.00982,0.009838,0.009808,0.009765,0.009698,0.009708,0.009679,0.009728,0.009852,0.009814,0.009737,0.009734,0.009727,0.009656]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M11] rank=11 service=checkoutservice metric=istio-latency-90 baseline=0.228048 peak=0.8875 signed_z=73.456 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=raw:[0.230909,0.231667,0.229474,0.2275,0.2455,0.243889,0.2194,0.220682,0.227895,0.226316,0.219062,0.222,0.221364,0.228,0.237778,0.244107,0.238281,0.230313,0.2095,0.235,0.236071,0.2215,0.211667,0.21125,0.23125,0.23275,0.224286,0.229194,0.228333,0.224286,0.228333,0.230645,0.23,0.5125,0.74,0.6875,0.65,0.489583,0.583333,0.86,0.792857,0.438889,0.33125,0.525,0.5375,0.6,0.8625,0.833333,0.728571,0.74375,0.75625,0.485714,0.457143,0.728571,0.728571,0.486538,0.5625,0.5,0.441667,0.4625,0.858333,0.875,0.85,0.766667]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M12] rank=12 service=frontend metric=istio-latency-90 baseline=0.207176 peak=0.884593 signed_z=58.365 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=raw:[0.222192,0.214647,0.206059,0.195988,0.207838,0.222465,0.21,0.183488,0.186689,0.197042,0.19634,0.201552,0.209745,0.218553,0.216625,0.209865,0.204205,0.201959,0.189364,0.185309,0.208143,0.219167,0.221059,0.206213,0.197445,0.209476,0.214382,0.219389,0.219077,0.214778,0.213713,0.206959,0.226386,0.73373,0.880488,0.765033,0.710429,0.725294,0.754969,0.874834,0.79918,0.487847,0.49439,0.507207,0.530288,0.583333,0.792246,0.834746,0.59569,0.494076,0.607364,0.606148,0.481278,0.52233,0.59087,0.520673,0.542105,0.591923,0.60155,0.593496,0.615702,0.618067,0.610714,0.578571]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[699.0,1440.0]

=== LOG SUMMARY ===
{"entries":[{"change_pct":50.0,"n_during":15,"n_pre":10,"service":"redis"},{"change_pct":3.8,"n_during":28707,"n_pre":27664,"service":"currencyservice"},{"change_pct":3.0,"n_during":31698,"n_pre":30770,"service":"frontend"},{"change_pct":2.8,"n_during":5345,"n_pre":5198,"service":"adservice"},{"change_pct":-1.9,"n_during":921,"n_pre":939,"service":"checkoutservice"},{"change_pct":-1.9,"n_during":307,"n_pre":313,"service":"emailservice"},{"change_pct":-1.9,"n_during":614,"n_pre":626,"service":"paymentservice"},{"change_pct":-1.8,"n_during":5176,"n_pre":5272,"service":"shippingservice"}],"mode":"volume","omitted_services":2,"service_count":10}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":177.9,"error_pct":0.0,"p95_during_ms":193.62144999999998,"p95_pre_ms":69.67875000000001,"service":"frontend","spans":204218},{"delta_pct":145.4,"error_pct":0.0,"p95_during_ms":203.95315,"p95_pre_ms":83.11494999999998,"service":"checkoutservice","spans":8682},{"delta_pct":31.4,"error_pct":0.0,"p95_during_ms":0.5280999999999992,"p95_pre_ms":0.402,"service":"paymentservice","spans":908},{"delta_pct":13.1,"error_pct":0.0,"p95_during_ms":5.212,"p95_pre_ms":4.61,"service":"recommendationservice","spans":26892},{"delta_pct":12.4,"error_pct":0.0,"p95_during_ms":0.281,"p95_pre_ms":0.25,"service":"currencyservice","spans":56646},{"delta_pct":-7.5,"error_pct":0.0,"p95_during_ms":0.40539999999999987,"p95_pre_ms":0.43839999999999996,"service":"emailservice","spans":1196},{"delta_pct":0.0,"error_pct":0.0,"p95_during_ms":0.023,"p95_pre_ms":0.023,"service":"productcatalogservice","spans":101422}],"omitted_services":0,"service_count":7}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=3 omitted_edges=2
[{"evidence_source":"metric","onset_rel_s":723.0,"rank":1,"service":"currencyservice","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":724.8,"rank":2,"service":"adservice","severity_z":14.456},{"evidence_source":"metric","onset_rel_s":733.8,"rank":3,"service":"cartservice","severity_z":426.305},{"evidence_source":"trace","onset_rel_s":735.0,"rank":4,"service":"recommendationservice","severity_z":6.601},{"evidence_source":"trace","onset_rel_s":735.0,"rank":5,"service":"checkoutservice","severity_z":17.918},{"evidence_source":"trace","onset_rel_s":735.0,"rank":6,"service":"frontend","severity_z":32.625},{"evidence_source":"metric","onset_rel_s":793.8,"rank":7,"service":"gke-gke-cluster-default-pool-2e1807ce-0e4z","severity_z":16.267},{"evidence_source":"trace","onset_rel_s":1005.0,"rank":8,"service":"paymentservice","severity_z":15.14},{"evidence_source":"metric","onset_rel_s":1078.2,"rank":9,"service":"gke-gke-cluster-default-pool-2e1807ce-w819","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1101.0,"rank":10,"service":"shippingservice","severity_z":16.133},{"evidence_source":"metric","onset_rel_s":1186.2,"rank":11,"service":"emailservice","severity_z":40.996},{"evidence_source":"metric","onset_rel_s":1186.2,"rank":12,"service":"gke-gke-cluster-default-pool-2e1807ce-cx8g","severity_z":33.64},{"evidence_source":"metric","onset_rel_s":1200.0,"rank":13,"service":"gke-gke-cluster-default-pool-2e1807ce-xte3","severity_z":33.049},{"evidence_source":"none","onset_rel_s":null,"rank":14,"service":"redis","severity_z":0.0}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"currencyservice","caller":"checkoutservice"},{"callee":"emailservice","caller":"checkoutservice"},{"callee":"paymentservice","caller":"checkoutservice"},{"callee":"checkoutservice","caller":"frontend"},{"callee":"currencyservice","caller":"frontend"},{"callee":"recommendationservice","caller":"frontend"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

## Assistant

{
"services": [
"currencyservice",
"checkoutservice",
"frontend"
],
"reason": "currencyservice is the root cause, evidenced by the earliest onset (rank 1) and extreme anomalies in container memory (mapped-file, cache) and sockets, which propagated latency degradation to its callers checkoutservice and frontend.",
"confidence": "high"
}

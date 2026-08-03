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
opaque_id: INC-92EB3EAF4583
observation_window={"duration_rel_s":1440.0,"source_metric_rows":1441}
selection_summary={"candidate_count":17,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":266,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["adservice","cartservice","checkoutservice","currencyservice","emailservice","frontend","frontend-external","gke-gke-cluster-default-pool-2e1807ce-0e4z","gke-gke-cluster-default-pool-2e1807ce-cx8g","gke-gke-cluster-default-pool-2e1807ce-w819","gke-gke-cluster-default-pool-2e1807ce-xte3","loadgenerator","paymentservice","productcatalogservice","recommendationservice","redis","shippingservice"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[11.25,33.75,56.25,78.75,101.25,123.75,146.25,168.75,191.25,213.75,236.25,258.75,281.25,303.75,326.25,348.75,371.25,393.75,416.25,438.75,461.25,483.75,506.25,528.75,551.25,573.75,596.25,618.75,641.25,663.75,686.25,708.75,731.25,753.75,776.25,798.75,821.25,843.75,866.25,888.75,911.25,933.75,956.25,978.75,1001.25,1023.75,1046.25,1068.75,1091.25,1113.75,1136.25,1158.75,1181.25,1203.75,1226.25,1248.75,1271.25,1293.75,1316.25,1338.75,1361.25,1383.75,1406.25,1428.75]
[M1] rank=1 service=productcatalogservice metric=container-memory-mapped-file baseline=0.0 peak=2207744.0 signed_z=999.0 onset_bin=32 onset_rel_s=731.25 persistence_bins=32
values_compact=rle:0*32,2207744*32
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M2] rank=2 service=recommendationservice metric=istio-latency-50 baseline=0.007456 peak=0.062177 signed_z=999.0 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=raw:[0.007504,0.007471,0.007444,0.007494,0.0075,0.007423,0.007436,0.007468,0.007474,0.007481,0.007453,0.00739,0.007392,0.00742,0.007442,0.007445,0.007461,0.007506,0.007491,0.007481,0.007556,0.0075,0.007398,0.007472,0.007474,0.007383,0.007388,0.007368,0.00739,0.007488,0.007491,0.007503,0.007516,0.009097,0.05274,0.057377,0.059086,0.057285,0.055856,0.056746,0.058673,0.061295,0.061359,0.060029,0.05874,0.061318,0.06032,0.051355,0.052349,0.058248,0.05943,0.059541,0.056914,0.05574,0.0575,0.057269,0.055489,0.056341,0.058551,0.056139,0.058121,0.060182,0.058115,0.061177]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M3] rank=3 service=productcatalogservice metric=istio-latency-90 baseline=0.004423 peak=0.08327 signed_z=999.0 onset_bin=32 onset_rel_s=731.25 persistence_bins=32
values_compact=raw:[0.004406,0.004402,0.004421,0.004416,0.004416,0.004421,0.004418,0.004422,0.004421,0.004425,0.004424,0.004408,0.004404,0.004404,0.004417,0.00442,0.004412,0.004411,0.004426,0.004432,0.004455,0.004451,0.004432,0.004438,0.004437,0.004427,0.004429,0.004424,0.004418,0.00443,0.004432,0.004452,0.004561,0.062888,0.080773,0.082814,0.083185,0.080941,0.080037,0.081041,0.081339,0.081665,0.082544,0.082493,0.082426,0.082421,0.081448,0.080517,0.080095,0.081858,0.08251,0.081889,0.080921,0.079879,0.080393,0.080428,0.080347,0.081067,0.081255,0.080925,0.080716,0.081544,0.082448,0.082086]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M4] rank=4 service=recommendationservice metric=istio-latency-90 baseline=0.009578 peak=0.092583 signed_z=999.0 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=raw:[0.009586,0.00954,0.009536,0.009597,0.00959,0.009544,0.009579,0.009648,0.009636,0.009596,0.00957,0.009507,0.009507,0.009535,0.009591,0.009586,0.009573,0.009578,0.009562,0.009582,0.009708,0.009698,0.009543,0.009585,0.009598,0.009514,0.009499,0.009535,0.009578,0.009615,0.009589,0.00962,0.009654,0.085693,0.090913,0.091475,0.091817,0.091457,0.091171,0.091349,0.091735,0.092259,0.092272,0.092006,0.091904,0.092409,0.092064,0.090271,0.09047,0.091814,0.092043,0.091908,0.091383,0.091148,0.0915,0.091454,0.091098,0.091268,0.09171,0.091228,0.091624,0.092036,0.091623,0.092235]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M5] rank=5 service=productcatalogservice metric=istio-latency-95 baseline=0.004719 peak=0.091635 signed_z=999.0 onset_bin=32 onset_rel_s=731.25 persistence_bins=32
values_compact=raw:[0.004708,0.004705,0.004715,0.004713,0.004714,0.004717,0.004715,0.004719,0.004719,0.004724,0.004722,0.004709,0.004705,0.004708,0.004715,0.004716,0.004711,0.004712,0.004721,0.004723,0.004739,0.004737,0.004724,0.004729,0.004729,0.004724,0.004724,0.004717,0.004713,0.004724,0.004726,0.004745,0.004848,0.081444,0.090387,0.091407,0.091592,0.090471,0.090018,0.09052,0.090669,0.090832,0.091272,0.091247,0.091213,0.09121,0.090724,0.090258,0.090048,0.090929,0.091255,0.090974,0.090493,0.089939,0.090197,0.090214,0.090173,0.090534,0.090643,0.090478,0.090372,0.090772,0.091308,0.091127]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M6] rank=6 service=recommendationservice metric=istio-latency-95 baseline=0.009843 peak=0.096384 signed_z=999.0 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=raw:[0.009846,0.009799,0.009798,0.00986,0.009851,0.009809,0.009847,0.00992,0.009907,0.00986,0.009835,0.009771,0.009772,0.009799,0.00986,0.009854,0.009838,0.009837,0.009821,0.009844,0.009977,0.009973,0.009811,0.00985,0.009864,0.00978,0.009763,0.009806,0.009852,0.00988,0.009851,0.009884,0.009921,0.093212,0.095685,0.095738,0.095909,0.095729,0.095586,0.095675,0.095867,0.096129,0.096136,0.096003,0.09605,0.096295,0.096032,0.095135,0.095235,0.096009,0.09612,0.095954,0.095691,0.095574,0.09575,0.095727,0.095549,0.095634,0.095855,0.095614,0.095812,0.096018,0.095811,0.096118]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M7] rank=7 service=productcatalogservice metric=istio-latency-99 baseline=0.004956 peak=0.098408 signed_z=999.0 onset_bin=31 onset_rel_s=708.75 persistence_bins=33
values_compact=delta:0.004949,-0.000001,0.000003,0,0,0.000002,0,0.000003,0.000002,0.000006,-0.000003,-0.000012,-0.000002,0.000005,0.000002,-0.000002,-0.000002,0.000003,0.000005,-0.000003,0.000012,-0.000001,-0.000011,0.000008,0,-0.000003,0,-0.000008,-0.000004,0.00001,0.000003,0.000018,0.053818,0.037492,0.001788,0.000204,0.000037,-0.000224,-0.00009,0.0001,0.00003,0.000032,0.000088,-0.000005,-0.000006,-0.000001,-0.000097,-0.000093,-0.000042,0.000176,0.000065,-0.000009,-0.000092,-0.000162,0.000051,0.000004,-0.000008,0.000072,0.000024,-0.00001,-0.000038,0.000071,0.000243,-0.000037
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M8] rank=8 service=cartservice metric=istio-latency-95 baseline=0.00504 peak=0.34625 signed_z=826.305 onset_bin=35 onset_rel_s=798.75 persistence_bins=15
values_compact=raw:[0.004933,0.004858,0.004842,0.004911,0.004969,0.004926,0.004853,0.004974,0.004983,0.006237,0.006631,0.004876,0.004852,0.004868,0.004924,0.004921,0.004889,0.004918,0.004938,0.004944,0.00547,0.004969,0.004884,0.004881,0.004884,0.004876,0.004889,0.004911,0.004914,0.004919,0.004896,0.005443,0.005653,0.004918,0.004965,0.008088,0.00811,0.005752,0.004972,0.004932,0.005585,0.053125,0.286979,0.1305,0.009705,0.008858,0.007843,0.007244,0.006164,0.007881,0.008063,0.0185,0.0244,0.005543,0.004998,0.004978,0.004997,0.004987,0.00677,0.006687,0.00497,0.004971,0.004976,0.004936]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M9] rank=9 service=productcatalogservice metric=container-sockets baseline=4.0 peak=6.0 signed_z=333.333 onset_bin=32 onset_rel_s=731.25 persistence_bins=32
values_compact=rle:4*32,6*32
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M10] rank=10 service=productcatalogservice metric=container-memory-cache baseline=20480.0 peak=2228224.0 signed_z=219.764 onset_bin=32 onset_rel_s=731.25 persistence_bins=32
values_compact=rle:20480*32,2228224*32
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M11] rank=11 service=frontend metric=istio-latency-50 baseline=0.045729 peak=0.193385 signed_z=147.862 onset_bin=31 onset_rel_s=708.75 persistence_bins=33
values_compact=raw:[0.045094,0.045485,0.046409,0.044561,0.044785,0.045925,0.045182,0.045232,0.0451,0.04514,0.045503,0.045108,0.0449,0.045296,0.045367,0.045548,0.045372,0.044829,0.045474,0.045241,0.046001,0.047148,0.046327,0.045916,0.045265,0.046134,0.046971,0.044989,0.045203,0.047387,0.046654,0.048779,0.049626,0.103156,0.16502,0.189972,0.19202,0.174511,0.1674,0.17047,0.178209,0.187574,0.190237,0.187707,0.187545,0.18895,0.184492,0.175,0.170853,0.17948,0.180018,0.184526,0.181496,0.166761,0.171411,0.16768,0.166365,0.176531,0.182513,0.178397,0.175,0.179696,0.184254,0.184558]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M12] rank=12 service=shippingservice metric=istio-latency-99 baseline=0.004967 peak=0.006225 signed_z=137.837 onset_bin=39 onset_rel_s=888.75 persistence_bins=2
values_compact=delta:0.00496,-0.000001,0,0,0,0,0.000021,0.000001,-0.000008,0.000014,-0.000004,-0.000013,-0.000011,0.000012,0,-0.000013,0,0.000001,0.000013,0,0,0,-0.000013,0.000012,0,-0.000013,0.000014,0,-0.000012,-0.000001,0,0,0.000025,0,0.000001,0.000011,-0.000025,-0.000012,0,0.000058,0.001008,-0.001054,-0.000013,0,0.000001,0.000013,0.00001,0.000005,-0.000014,-0.000014,0,0.000012,0.000023,-0.000012,-0.000023,0,0,0,0.000013,0.000001,-0.000002,-0.000001,0,0.000001
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[701.0,1440.0]

=== LOG SUMMARY ===
{"entries":[{"change_pct":50.0,"n_during":15,"n_pre":10,"service":"redis"},{"change_pct":4.2,"n_during":28789,"n_pre":27630,"service":"currencyservice"},{"change_pct":2.7,"n_during":32093,"n_pre":31257,"service":"frontend"},{"change_pct":2.1,"n_during":5387,"n_pre":5277,"service":"adservice"},{"change_pct":2.0,"n_during":9278,"n_pre":9098,"service":"cartservice"},{"change_pct":1.7,"n_during":5446,"n_pre":5354,"service":"shippingservice"},{"change_pct":1.6,"n_during":6756,"n_pre":6648,"service":"recommendationservice"},{"change_pct":0.0,"n_during":1032,"n_pre":1032,"service":"checkoutservice"}],"mode":"volume","omitted_services":2,"service_count":10}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":1591.3,"error_pct":0.0,"p95_during_ms":83.8653,"p95_pre_ms":4.95875,"service":"recommendationservice","spans":27384},{"delta_pct":194.2,"error_pct":0.0,"p95_during_ms":173.2650999999998,"p95_pre_ms":58.8899,"service":"frontend","spans":206326},{"delta_pct":48.8,"error_pct":0.0,"p95_during_ms":112.418,"p95_pre_ms":75.543,"service":"checkoutservice","spans":9342},{"delta_pct":14.3,"error_pct":0.0,"p95_during_ms":0.032,"p95_pre_ms":0.028,"service":"productcatalogservice","spans":102928},{"delta_pct":10.7,"error_pct":0.0,"p95_during_ms":0.40574999999999983,"p95_pre_ms":0.3665499999999999,"service":"paymentservice","spans":976},{"delta_pct":8.6,"error_pct":0.0,"p95_during_ms":0.42524999999999974,"p95_pre_ms":0.39170000000000005,"service":"emailservice","spans":1264},{"delta_pct":0.4,"error_pct":0.0,"p95_during_ms":0.231,"p95_pre_ms":0.23,"service":"currencyservice","spans":56702}],"omitted_services":0,"service_count":7}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=3 omitted_edges=2
[{"evidence_source":"metric","onset_rel_s":720.0,"rank":1,"service":"gke-gke-cluster-default-pool-2e1807ce-cx8g","severity_z":17.478},{"evidence_source":"metric","onset_rel_s":724.8,"rank":2,"service":"productcatalogservice","severity_z":999.0},{"evidence_source":"trace","onset_rel_s":735.0,"rank":3,"service":"recommendationservice","severity_z":162.31},{"evidence_source":"trace","onset_rel_s":735.0,"rank":4,"service":"frontend","severity_z":24.334},{"evidence_source":"trace","onset_rel_s":735.0,"rank":5,"service":"checkoutservice","severity_z":6.952},{"evidence_source":"metric","onset_rel_s":757.2,"rank":6,"service":"currencyservice","severity_z":10.259},{"evidence_source":"metric","onset_rel_s":808.2,"rank":7,"service":"adservice","severity_z":121.934},{"evidence_source":"metric","onset_rel_s":907.2,"rank":8,"service":"shippingservice","severity_z":137.837},{"evidence_source":"metric","onset_rel_s":946.8,"rank":9,"service":"cartservice","severity_z":826.305},{"evidence_source":"metric","onset_rel_s":1069.2,"rank":10,"service":"gke-gke-cluster-default-pool-2e1807ce-0e4z","severity_z":103.498},{"evidence_source":"trace","onset_rel_s":1095.0,"rank":11,"service":"paymentservice","severity_z":10.408},{"evidence_source":"metric","onset_rel_s":1108.8,"rank":12,"service":"redis","severity_z":12.823},{"evidence_source":"metric","onset_rel_s":1363.2,"rank":13,"service":"emailservice","severity_z":58.079},{"evidence_source":"none","onset_rel_s":null,"rank":14,"service":"gke-gke-cluster-default-pool-2e1807ce-xte3","severity_z":0.0}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"currencyservice","caller":"checkoutservice"},{"callee":"emailservice","caller":"checkoutservice"},{"callee":"paymentservice","caller":"checkoutservice"},{"callee":"productcatalogservice","caller":"checkoutservice"},{"callee":"checkoutservice","caller":"frontend"},{"callee":"currencyservice","caller":"frontend"},{"callee":"productcatalogservice","caller":"frontend"},{"callee":"recommendationservice","caller":"frontend"},{"callee":"productcatalogservice","caller":"recommendationservice"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

{"confidence":"high","reason":"Rank productcatalogservice first because productcatalogservice has direct container-memory-mapped-file evidence (signed-z 999, persistence 32 bins); although recommendationservice is salient, the caller path recommendationservice -> productcatalogservice means a disturbance in the callee can propagate back toward that caller-side symptom.","services":["productcatalogservice","recommendationservice"]}

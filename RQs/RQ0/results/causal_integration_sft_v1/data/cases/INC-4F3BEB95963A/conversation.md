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
opaque_id: INC-4F3BEB95963A
observation_window={"duration_rel_s":1440.0,"source_metric_rows":1441}
selection_summary={"candidate_count":17,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":263,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["adservice","cartservice","checkoutservice","currencyservice","emailservice","frontend","frontend-external","gke-gke-cluster-default-pool-2e1807ce-0e4z","gke-gke-cluster-default-pool-2e1807ce-cx8g","gke-gke-cluster-default-pool-2e1807ce-w819","gke-gke-cluster-default-pool-2e1807ce-xte3","loadgenerator","paymentservice","productcatalogservice","recommendationservice","redis","shippingservice"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[11.25,33.75,56.25,78.75,101.25,123.75,146.25,168.75,191.25,213.75,236.25,258.75,281.25,303.75,326.25,348.75,371.25,393.75,416.25,438.75,461.25,483.75,506.25,528.75,551.25,573.75,596.25,618.75,641.25,663.75,686.25,708.75,731.25,753.75,776.25,798.75,821.25,843.75,866.25,888.75,911.25,933.75,956.25,978.75,1001.25,1023.75,1046.25,1068.75,1091.25,1113.75,1136.25,1158.75,1181.25,1203.75,1226.25,1248.75,1271.25,1293.75,1316.25,1338.75,1361.25,1383.75,1406.25,1428.75]
[M1] rank=1 service=frontend metric=istio-latency-50 baseline=0.045366 peak=1.53331 signed_z=999.0 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=raw:[0.046002,0.046542,0.046445,0.044879,0.046573,0.046627,0.044816,0.04432,0.045027,0.044913,0.045464,0.045441,0.045427,0.045712,0.044148,0.043382,0.044187,0.045001,0.044679,0.046094,0.045796,0.044509,0.045345,0.046832,0.04655,0.045731,0.045842,0.045553,0.044847,0.045045,0.045048,0.045,0.046567,0.085671,1.307965,1.493421,1.48913,1.474036,1.415899,1.419184,1.475182,1.486739,1.431131,1.43209,1.475854,1.495896,1.505917,1.479955,1.47023,1.438285,1.403587,1.440902,1.494868,1.530664,1.507225,1.488006,1.486047,1.443563,1.45,1.474601,1.476562,1.479198,1.492764,1.51413]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M2] rank=2 service=productcatalogservice metric=istio-latency-50 baseline=0.001765 peak=0.101406 signed_z=999.0 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=raw:[0.001859,0.001927,0.001819,0.001728,0.001717,0.001716,0.001656,0.001616,0.001658,0.001686,0.001684,0.001673,0.00175,0.001787,0.001716,0.001716,0.001774,0.00181,0.00181,0.001783,0.001781,0.001754,0.001756,0.00176,0.001802,0.001825,0.00184,0.001881,0.001856,0.001811,0.001808,0.001777,0.00182,0.002341,0.004876,0.005,0.005,0.100207,0.004959,0.100203,0.100569,0.004996,0.100094,0.100087,0.100323,0.004988,0.004982,0.100721,0.004993,0.004998,0.004993,0.100152,0.100293,0.004995,0.100057,0.004994,0.004988,0.004959,0.100179,0.100569,0.10009,0.10006,0.10006,0.100029]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M3] rank=3 service=recommendationservice metric=istio-latency-50 baseline=0.007107 peak=0.175875 signed_z=999.0 onset_bin=32 onset_rel_s=731.25 persistence_bins=32
values_compact=delta:0.007315,0.000015,-0.000033,-0.000083,-0.000012,-0.000068,-0.00001,-0.000039,-0.00004,-0.000065,-0.000005,0.00002,0.000009,0.000002,0.000002,0.000051,0.000008,0.000034,0.00006,0.00008,-0.000047,-0.000111,-0.000042,-0.000035,0.000003,0.000027,0.00003,0.000016,-0.000038,-0.000041,0.000127,0.000215,0.000133,0.00189,0.159305,0.006327,0.00054,0.000126,-0.00055,-0.000116,0,0,0,0,0,0,0,0,0,0,0.000336,0.000357,-0.000363,0.000521,0.000022,-0.000638,0.000002,-0.000237,0,0.000444,0.000006,-0.00045,0.000628,0.000013
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M4] rank=4 service=productcatalogservice metric=istio-latency-90 baseline=0.004368 peak=0.220375 signed_z=999.0 onset_bin=32 onset_rel_s=731.25 persistence_bins=32
values_compact=raw:[0.004388,0.004406,0.004373,0.004355,0.004369,0.004367,0.004339,0.004333,0.004345,0.004348,0.004343,0.004343,0.004356,0.004363,0.004355,0.004358,0.004376,0.004382,0.004376,0.004368,0.004373,0.004367,0.004371,0.004373,0.004399,0.004401,0.004382,0.004392,0.004381,0.004374,0.004375,0.004365,0.004614,0.173229,0.219737,0.219954,0.219983,0.220089,0.219856,0.220041,0.220114,0.219987,0.220019,0.220017,0.220065,0.219935,0.219928,0.220144,0.219956,0.219984,0.219976,0.22003,0.220059,0.220163,0.220192,0.220012,0.220006,0.219863,0.220131,0.220205,0.220113,0.220012,0.220012,0.220006]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M5] rank=5 service=recommendationservice metric=istio-latency-90 baseline=0.009494 peak=0.236574 signed_z=999.0 onset_bin=32 onset_rel_s=731.25 persistence_bins=32
values_compact=delta:0.009561,0.000064,-0.00001,-0.000072,0.000018,-0.000048,-0.000066,-0.000012,-0.000014,0.000001,0.000031,0.000037,-0.000013,-0.000053,-0.000009,0.000025,0.000025,0.000005,0.000084,0.000055,-0.000055,-0.000066,-0.000047,0.000006,0.000047,0.000047,-0.000012,-0.00005,-0.000059,0.000004,0.000075,0.000058,0.000314,0.208319,0.016599,0.000211,0.000971,0.000227,-0.00099,-0.000208,0,0,0,0,0,0,0,0,0,0,0.000604,0.000644,-0.000654,0.000938,0.00004,-0.001149,0.000004,-0.000427,0,0.000799,0.000012,-0.000811,0.001131,0.000023
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M6] rank=6 service=productcatalogservice metric=istio-latency-95 baseline=0.004693 peak=0.235294 signed_z=999.0 onset_bin=32 onset_rel_s=731.25 persistence_bins=32
values_compact=raw:[0.004706,0.004716,0.004693,0.004684,0.0047,0.004698,0.004674,0.004673,0.004681,0.004681,0.004675,0.004677,0.004681,0.004684,0.004683,0.004688,0.004701,0.004704,0.004696,0.004692,0.004698,0.004694,0.004698,0.004699,0.004723,0.004722,0.0047,0.004706,0.004696,0.004694,0.004696,0.004688,0.004963,0.211975,0.235033,0.234977,0.234997,0.235074,0.234936,0.23502,0.235057,0.234994,0.235009,0.235009,0.235032,0.234968,0.234964,0.235072,0.234978,0.234992,0.234988,0.235015,0.235029,0.235194,0.235209,0.235035,0.235033,0.234932,0.235077,0.235159,0.235116,0.235006,0.235006,0.235003]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M7] rank=7 service=recommendationservice metric=istio-latency-95 baseline=0.009793 peak=0.244162 signed_z=999.0 onset_bin=32 onset_rel_s=731.25 persistence_bins=32
values_compact=delta:0.009842,0.00007,-0.00001,-0.000069,0.000023,-0.000047,-0.000073,-0.000006,-0.000012,0.000007,0.000038,0.000039,-0.000016,-0.00006,-0.000011,0.000023,0.000027,0.000001,0.000087,0.000052,-0.000056,-0.00006,-0.000048,0.000011,0.000053,0.000049,-0.000016,-0.000061,-0.00006,0.000005,0.000074,0.000038,0.112309,0.114538,0.006373,-0.000554,0.001025,0.00024,-0.001045,-0.00022,0,0,0,0,0,0,0,0,0,0,0.000638,0.000679,-0.00069,0.00099,0.000042,-0.001212,0.000004,-0.000451,0,0.000843,0.000013,-0.000856,0.001194,0.000024
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M8] rank=8 service=productcatalogservice metric=istio-latency-99 baseline=0.004954 peak=0.24727 signed_z=999.0 onset_bin=32 onset_rel_s=731.25 persistence_bins=32
values_compact=delta:0.004958,0.000006,-0.000015,-0.000002,0.000018,-0.000003,-0.000019,0.000001,0.000005,-0.000002,-0.000006,0.000003,0,-0.000002,0.000005,0.000006,0.000009,-0.000001,-0.000008,-0.000002,0.000006,-0.000002,0.000004,0.000001,0.000023,-0.000003,-0.000026,0.000003,-0.000008,0.000001,0.000002,-0.000005,0.210514,0.02751,0.004049,-0.000025,0.000004,0.000063,-0.000026,-0.000032,0.000007,-0.000012,0.000003,0,0.000004,-0.000012,-0.000001,0.000021,-0.000018,0.000002,0,0.000005,0.000003,0.000213,0.000004,-0.000169,0.000001,-0.000069,0.000029,0.000108,-0.000004,-0.000118,0,0
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M9] rank=9 service=cartservice metric=container-sockets baseline=4.0 peak=6.0 signed_z=333.333 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=rle:4*46,6*1,4*17
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M10] rank=10 service=frontend metric=container-sockets baseline=25.0 peak=34.0 signed_z=264.706 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=rle:25*33,28*1,31*1,32*5,33*2,34*22
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M11] rank=11 service=paymentservice metric=istio-latency-90 baseline=0.007878 peak=0.2275 signed_z=219.601 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=raw:[0.008563,0.0072,0.004825,0.0085,0.009625,0.009087,0.009083,0.009222,0.008222,0.009,0.009056,0.007611,0.007,0.00725,0.007667,0.008417,0.008458,0.008346,0.008308,0.008676,0.008538,0.0075,0.0079,0.0064,0.0056,0.007846,0.008071,0.007714,0.0064,0.005417,0.007375,0.0075,0.006417,0.007643,0.00855,0.008182,0.01,0.2275,0.008833,0.007875,0.007333,0.00825,0.0071,0.006667,0.006625,0.0081,0.007833,0.007071,0.007214,0.007143,0.008292,0.00855,0.007857,0.008056,0.00725,0.008846,0.008885,0.0062,0.007222,0.008042,0.008,0.008417,0.008187,0.0065]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M12] rank=12 service=frontend metric=istio-latency-90 baseline=0.171015 peak=2.310028 signed_z=143.713 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=raw:[0.16358,0.209637,0.210545,0.168404,0.175517,0.176847,0.159206,0.147905,0.150357,0.163975,0.173558,0.174138,0.18027,0.173761,0.163122,0.164194,0.168005,0.16764,0.170238,0.189678,0.178063,0.163372,0.170347,0.171361,0.174187,0.185684,0.175144,0.155339,0.148201,0.149914,0.177569,0.176457,0.186713,1.916981,2.261593,2.298684,2.303043,2.301929,2.28871,2.291088,2.302044,2.301092,2.290048,2.300746,2.305869,2.299923,2.301183,2.29613,2.298609,2.294351,2.282511,2.28818,2.298974,2.309175,2.304913,2.298182,2.30093,2.291528,2.29,2.298403,2.298884,2.299406,2.302026,2.302826]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[734.0,1440.0]

=== LOG SUMMARY ===
{"entries":[{"change_pct":50.0,"n_during":15,"n_pre":10,"service":"redis"},{"change_pct":-26.3,"n_during":21159,"n_pre":28709,"service":"currencyservice"},{"change_pct":-24.5,"n_during":24436,"n_pre":32374,"service":"frontend"},{"change_pct":-24.2,"n_during":4117,"n_pre":5433,"service":"adservice"},{"change_pct":-23.2,"n_during":7220,"n_pre":9396,"service":"cartservice"},{"change_pct":-23.1,"n_during":5289,"n_pre":6878,"service":"recommendationservice"},{"change_pct":-22.9,"n_during":4292,"n_pre":5566,"service":"shippingservice"},{"change_pct":-17.0,"n_during":288,"n_pre":347,"service":"emailservice"}],"mode":"volume","omitted_services":2,"service_count":10}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":4110.0,"error_pct":0.0,"p95_during_ms":204.68885,"p95_pre_ms":4.862,"service":"recommendationservice","spans":24914},{"delta_pct":2254.4,"error_pct":0.0,"p95_during_ms":1442.0452,"p95_pre_ms":61.24929999999996,"service":"frontend","spans":185191},{"delta_pct":234.0,"error_pct":0.0,"p95_during_ms":240.83024999999998,"p95_pre_ms":72.10419999999993,"service":"checkoutservice","spans":8665},{"delta_pct":33.3,"error_pct":0.0,"p95_during_ms":0.032,"p95_pre_ms":0.024,"service":"productcatalogservice","spans":93140},{"delta_pct":-7.0,"error_pct":0.0,"p95_during_ms":0.4193499999999998,"p95_pre_ms":0.45110000000000006,"service":"emailservice","spans":1211},{"delta_pct":6.0,"error_pct":0.0,"p95_during_ms":0.229,"p95_pre_ms":0.216,"service":"currencyservice","spans":50156},{"delta_pct":-2.7,"error_pct":0.0,"p95_during_ms":0.5411999999999999,"p95_pre_ms":0.5564,"service":"paymentservice","spans":923}],"omitted_services":0,"service_count":7}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=3 omitted_edges=2
[{"evidence_source":"metric","onset_rel_s":723.0,"rank":1,"service":"emailservice","severity_z":48.143},{"evidence_source":"trace","onset_rel_s":735.0,"rank":2,"service":"frontend","severity_z":256.431},{"evidence_source":"trace","onset_rel_s":735.0,"rank":3,"service":"recommendationservice","severity_z":436.607},{"evidence_source":"trace","onset_rel_s":735.0,"rank":4,"service":"checkoutservice","severity_z":38.125},{"evidence_source":"metric","onset_rel_s":796.2,"rank":5,"service":"currencyservice","severity_z":40.18},{"evidence_source":"metric","onset_rel_s":823.2,"rank":6,"service":"paymentservice","severity_z":219.601},{"evidence_source":"trace","onset_rel_s":915.0,"rank":7,"service":"productcatalogservice","severity_z":4.306},{"evidence_source":"metric","onset_rel_s":1033.8,"rank":8,"service":"cartservice","severity_z":333.333},{"evidence_source":"none","onset_rel_s":null,"rank":9,"service":"gke-gke-cluster-default-pool-2e1807ce-0e4z","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":10,"service":"redis","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":11,"service":"adservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":12,"service":"gke-gke-cluster-default-pool-2e1807ce-cx8g","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":13,"service":"shippingservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":14,"service":"gke-gke-cluster-default-pool-2e1807ce-w819","severity_z":0.0}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"currencyservice","caller":"checkoutservice"},{"callee":"emailservice","caller":"checkoutservice"},{"callee":"paymentservice","caller":"checkoutservice"},{"callee":"productcatalogservice","caller":"checkoutservice"},{"callee":"checkoutservice","caller":"frontend"},{"callee":"currencyservice","caller":"frontend"},{"callee":"productcatalogservice","caller":"frontend"},{"callee":"recommendationservice","caller":"frontend"},{"callee":"productcatalogservice","caller":"recommendationservice"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

{"confidence":"high","reason":"Rank productcatalogservice first because productcatalogservice has direct istio-latency-50 evidence (signed-z 999, persistence 31 bins); although frontend is salient, the caller path frontend -> productcatalogservice means a disturbance in the callee can propagate back toward that caller-side symptom.","services":["productcatalogservice","frontend"]}

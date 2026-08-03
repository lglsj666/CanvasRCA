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
opaque_id: INC-1967370045A5
observation_window={"duration_rel_s":1440.0,"source_metric_rows":1441}
selection_summary={"candidate_count":17,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":261,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["adservice","cartservice","checkoutservice","currencyservice","emailservice","frontend","frontend-external","gke-gke-cluster-default-pool-2e1807ce-0e4z","gke-gke-cluster-default-pool-2e1807ce-cx8g","gke-gke-cluster-default-pool-2e1807ce-w819","gke-gke-cluster-default-pool-2e1807ce-xte3","loadgenerator","paymentservice","productcatalogservice","recommendationservice","redis","shippingservice"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[11.25,33.75,56.25,78.75,101.25,123.75,146.25,168.75,191.25,213.75,236.25,258.75,281.25,303.75,326.25,348.75,371.25,393.75,416.25,438.75,461.25,483.75,506.25,528.75,551.25,573.75,596.25,618.75,641.25,663.75,686.25,708.75,731.25,753.75,776.25,798.75,821.25,843.75,866.25,888.75,911.25,933.75,956.25,978.75,1001.25,1023.75,1046.25,1068.75,1091.25,1113.75,1136.25,1158.75,1181.25,1203.75,1226.25,1248.75,1271.25,1293.75,1316.25,1338.75,1361.25,1383.75,1406.25,1428.75]
[M1] rank=1 service=emailservice metric=container-memory-failures-total baseline=0.051669 peak=220055.854766 signed_z=999.0 onset_bin=32 onset_rel_s=731.25 persistence_bins=32
values_compact=delta:0,0,0,0,0,0,0.220702,0.071262,-0.002187,-0.250687,-0.03909,0,0,0,0,0,0,0.25,-0.034992,-0.215008,0,0,0,0,0,0,0,0,0,0.235994,-0.026061,-0.171021,20182.266616,107333.877935,88540.436746,-17706.701557,4677.151279,12736.654935,-5167.872982,515.487142,-5096.969212,-4140.539202,249.733513,13843.377707,-10278.759069,-14175.171698,9931.363225,-1931.286695,-3645.17151,-252.53147,-40309.140114,58835.042203,-3653.336192,-9366.290395,-33699.253944,38941.063027,4911.696946,2053.108841,-6678.819918,-5416.28173,3797.497438,-2859.489155,281.345938,-1266.845833
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M2] rank=2 service=emailservice metric=container-memory-mapped-file baseline=0.0 peak=2293760.0 signed_z=999.0 onset_bin=32 onset_rel_s=731.25 persistence_bins=32
values_compact=rle:0*32,2293760*32
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M3] rank=3 service=emailservice metric=container-memory-rss baseline=41213559.466667 peak=261738496.0 signed_z=999.0 onset_bin=6 onset_rel_s=146.25 persistence_bins=35
values_compact=delta:41213952,0,0,0,0,0,-4096,0,4096,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,-4096,4096,0,1482752,40796160,131702784,46542848,0,-28672,-4096,-77135872,77135872,0,4096,-75853824,75853824,-8192,-174010368,174018560,0,-218902528,218898432,-15439872,-15439872,30883840,-28672,28672,-17199104,-166535168,175325184,8404992,-150659072,150663168,-4096,4096
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M4] rank=4 service=emailservice metric=container-memory-usage-bytes baseline=42194028.088889 peak=268439552.0 signed_z=999.0 onset_bin=32 onset_rel_s=731.25 persistence_bins=32
values_compact=delta:42192896,0,0,8192,-8192,4096,-8192,0,4096,0,0,0,0,0,4096,0,-4096,0,4096,-4096,0,4096,0,-4096,0,0,0,4096,0,-8192,4096,4096,5410816,42582016,131710976,46538752,-4096,0,0,-77139968,77139968,0,0,-75726848,75726848,0,-173817856,173817856,0,-221405184,221405184,-15441920,-15441920,30883840,-16384,16384,-17199104,-166535168,175562752,8171520,-150663168,150667264,-4096,0
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M5] rank=5 service=emailservice metric=container-memory-working-set-bytes baseline=42194028.088889 peak=268439552.0 signed_z=999.0 onset_bin=32 onset_rel_s=731.25 persistence_bins=32
values_compact=delta:42192896,0,0,8192,-8192,4096,-8192,0,4096,0,0,0,0,0,4096,0,-4096,0,4096,-4096,0,4096,0,-4096,0,0,0,4096,0,-8192,4096,4096,5410816,42582016,131710976,46538752,-4096,0,0,-77139968,77139968,0,0,-75726848,75726848,0,-173817856,173817856,0,-221405184,221405184,-15441920,-15441920,30883840,-16384,16384,-17199104,-166535168,175562752,8171520,-150663168,150667264,-4096,0
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M6] rank=6 service=emailservice metric=istio-latency-50 baseline=0.003054 peak=0.6875 signed_z=999.0 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=raw:[0.003,0.003,0.003,0.003048,0.003043,0.003,0.003049,0.003041,0.003,0.003,0.003089,0.003095,0.003171,0.003133,0.003044,0.003041,0.003035,0.003038,0.0031,0.003162,0.003093,0.003054,0.003067,0.003051,0.00313,0.003154,0.003,0.003051,0.003051,0.003,0.003,0.003,0.003,0.0035,0.09375,0.1,0.08125,0.175,0.095,0.0625,0.1,0.375,0.078125,0.15,0.19375,0.5,0.6875,0.40625,0.270833,0.085,0.076562,0.089286,0.1,0.0875,0.086111,0.060714,0.06,0.05,0.066667,0.4375,0.375,0.075,0.075,0.55]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M7] rank=7 service=emailservice metric=istio-latency-90 baseline=0.004698 peak=2.17 signed_z=999.0 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=raw:[0.0046,0.0046,0.0046,0.004686,0.004677,0.0046,0.004688,0.004673,0.0046,0.0046,0.00476,0.004771,0.004909,0.00484,0.00468,0.004673,0.004663,0.004668,0.00478,0.004892,0.004767,0.004697,0.00472,0.004692,0.004835,0.004877,0.0046,0.004692,0.004692,0.0046,0.0046,0.0046,0.0046,0.075,2.092857,2.028571,1.87,1.925,1.557143,1.5,1.872727,1.95,1.5625,1.675,2.005,2.071429,2.10625,2.17,2.05,1.7875,1.45,0.9875,0.933333,1.7125,1.7125,0.4875,0.84,1.075,1.5625,2.025,2.05,1.8625,1.8625,1.93]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M8] rank=8 service=emailservice metric=istio-latency-95 baseline=0.005099 peak=2.625 signed_z=999.0 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=raw:[0.0048,0.0048,0.0048,0.00489,0.004881,0.0048,0.004893,0.004878,0.0048,0.0048,0.004969,0.004981,0.006833,0.006,0.004884,0.004878,0.004867,0.004872,0.00499,0.006667,0.004977,0.004903,0.004927,0.004897,0.005917,0.0065,0.0048,0.004897,0.004897,0.0048,0.0048,0.0048,0.0048,1.375,2.296429,2.264286,2.185,2.2125,2.028571,2.0,2.186364,2.225,2.03125,2.0875,2.2525,2.285714,2.303125,2.485,2.489286,2.14375,1.975,1.7125,1.45,2.10625,2.10625,0.975,1.15,1.7875,2.03125,2.2625,2.275,2.18125,2.18125,2.215]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M9] rank=9 service=emailservice metric=istio-latency-99 baseline=0.007274 peak=4.525 signed_z=999.0 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=raw:[0.00496,0.00496,0.00496,0.00785,0.0076,0.00496,0.0079,0.0075,0.00496,0.00496,0.008825,0.0089,0.009367,0.0092,0.0077,0.0075,0.0071,0.0073,0.00895,0.009333,0.008875,0.0081,0.00845,0.008,0.009183,0.0093,0.00496,0.008,0.008,0.00496,0.00496,0.00496,0.00496,2.275,2.459286,2.452857,2.437,2.4425,2.405714,2.4,2.437273,2.445,2.40625,2.4175,2.4505,2.457143,2.460625,4.475,4.4875,2.42875,2.395,2.3425,2.29,2.42125,2.42125,2.185,2.23,2.3575,2.40625,2.4525,2.455,2.43625,2.43625,2.443]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M10] rank=10 service=productcatalogservice metric=istio-latency-99 baseline=0.004953 peak=0.019406 signed_z=999.0 onset_bin=33 onset_rel_s=753.75 persistence_bins=27
values_compact=delta:0.004954,-0.000005,0,0.000004,-0.000002,0.000001,0.000004,-0.000005,-0.000006,0.000001,0.000009,0.000001,0,0.00003,-0.000011,-0.000028,0.000004,0.000007,-0.000003,-0.000012,0.000003,0.000002,0,-0.000002,0.000003,0.000004,-0.000003,0.000017,0.000002,-0.000023,-0.000001,0,-0.000001,0.000042,0.000005,-0.000003,-0.000001,-0.000021,0.000025,0.000001,0.003269,0.000501,-0.003781,0.000001,0.000397,-0.000381,-0.00002,0.000009,0.000012,0.000356,-0.000369,0.000004,0.000009,-0.00001,0.00001,0.013251,0,-0.004275,-0.006125,0.003185,0.001268,-0.006377,-0.000927,0.001968
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M11] rank=11 service=shippingservice metric=istio-latency-99 baseline=0.004967 peak=0.069625 signed_z=999.0 onset_bin=34 onset_rel_s=776.25 persistence_bins=22
values_compact=raw:[0.00497,0.004958,0.004957,0.004958,0.004958,0.004982,0.004983,0.004969,0.004968,0.004956,0.004957,0.004958,0.004984,0.004996,0.004969,0.004957,0.004956,0.004981,0.004994,0.004972,0.004957,0.004958,0.004958,0.004956,0.004956,0.004957,0.004957,0.004996,0.004995,0.004955,0.004955,0.004956,0.004971,0.00497,0.033625,0.0315,0.014125,0.013975,0.0191,0.023912,0.004981,0.0076,0.0098,0.005,0.009767,0.00972,0.008537,0.004997,0.008525,0.01775,0.02295,0.0235,0.004987,0.004985,0.004971,0.004993,0.00905,0.024175,0.0615,0.01865,0.01,0.004996,0.007,0.006033]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M12] rank=12 service=emailservice metric=container-cpu-system-seconds-total baseline=0.068682 peak=13.15626 signed_z=898.143 onset_bin=32 onset_rel_s=731.25 persistence_bins=32
values_compact=delta:0.059663,0.002002,-0.013912,0.004343,0.015323,0.016088,0.004124,-0.004363,-0.01817,-0.001823,0.002806,-0.000205,0.012121,0.003083,-0.004274,-0.023731,0.01966,-0.02803,0.009592,0.026553,0.008609,-0.00444,0.01061,-0.029757,0.015226,-0.032676,0.01688,0.00539,0.004257,-0.016709,-0.004037,0.020704,1.414075,5.474844,4.684496,-0.265723,0.01442,0.513788,-0.05517,-0.152546,0.133678,0.204689,0.23735,-0.289811,0.271129,-0.140828,-0.319905,0.308348,0,0.005328,-1.884267,2.582925,-0.647374,0.208755,-1.430616,1.928557,-0.011897,-0.31074,0.1444,0.156006,-0.018409,0.164723,0.083821,-0.230643
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[703.0,1440.0]

=== LOG SUMMARY ===
{"entries":[{"change_pct":8.9,"n_during":29517,"n_pre":27095,"service":"currencyservice"},{"change_pct":6.7,"n_during":32710,"n_pre":30651,"service":"frontend"},{"change_pct":-5.4,"n_during":948,"n_pre":1002,"service":"checkoutservice"},{"change_pct":-5.4,"n_during":316,"n_pre":334,"service":"emailservice"},{"change_pct":-5.4,"n_during":632,"n_pre":668,"service":"paymentservice"},{"change_pct":5.1,"n_during":9432,"n_pre":8971,"service":"cartservice"},{"change_pct":4.8,"n_during":5530,"n_pre":5276,"service":"adservice"},{"change_pct":3.9,"n_during":6875,"n_pre":6618,"service":"recommendationservice"}],"mode":"volume","omitted_services":2,"service_count":10}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":13700.8,"error_pct":0.0,"p95_during_ms":70.4875,"p95_pre_ms":0.51075,"service":"emailservice","spans":1115},{"delta_pct":583.7,"error_pct":0.0,"p95_during_ms":489.283,"p95_pre_ms":71.56820000000002,"service":"checkoutservice","spans":8771},{"delta_pct":20.1,"error_pct":0.0,"p95_during_ms":5.7335,"p95_pre_ms":4.7722999999999995,"service":"recommendationservice","spans":26784},{"delta_pct":15.5,"error_pct":0.0,"p95_during_ms":61.58119999999995,"p95_pre_ms":53.329799999999985,"service":"frontend","spans":201808},{"delta_pct":9.0,"error_pct":0.0,"p95_during_ms":0.4908499999999993,"p95_pre_ms":0.45025000000000004,"service":"paymentservice","spans":920},{"delta_pct":3.6,"error_pct":0.0,"p95_during_ms":0.029,"p95_pre_ms":0.028,"service":"productcatalogservice","spans":100812},{"delta_pct":0.1,"error_pct":0.0,"p95_during_ms":0.21625,"p95_pre_ms":0.216,"service":"currencyservice","spans":55313}],"omitted_services":0,"service_count":7}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=3 omitted_edges=1
[{"evidence_source":"trace","onset_rel_s":735.0,"rank":1,"service":"emailservice","severity_z":999.0},{"evidence_source":"trace","onset_rel_s":735.0,"rank":2,"service":"checkoutservice","severity_z":125.362},{"evidence_source":"metric","onset_rel_s":759.0,"rank":3,"service":"gke-gke-cluster-default-pool-2e1807ce-cx8g","severity_z":44.965},{"evidence_source":"trace","onset_rel_s":855.0,"rank":4,"service":"recommendationservice","severity_z":46.364},{"evidence_source":"metric","onset_rel_s":922.8,"rank":5,"service":"frontend","severity_z":43.478},{"evidence_source":"metric","onset_rel_s":1131.0,"rank":6,"service":"shippingservice","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1231.8,"rank":7,"service":"productcatalogservice","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1278.0,"rank":8,"service":"adservice","severity_z":156.313},{"evidence_source":"metric","onset_rel_s":1380.0,"rank":9,"service":"paymentservice","severity_z":51.16},{"evidence_source":"none","onset_rel_s":null,"rank":10,"service":"gke-gke-cluster-default-pool-2e1807ce-w819","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":11,"service":"currencyservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":12,"service":"gke-gke-cluster-default-pool-2e1807ce-xte3","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":13,"service":"cartservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":14,"service":"gke-gke-cluster-default-pool-2e1807ce-0e4z","severity_z":0.0}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"currencyservice","caller":"checkoutservice"},{"callee":"emailservice","caller":"checkoutservice"},{"callee":"paymentservice","caller":"checkoutservice"},{"callee":"productcatalogservice","caller":"checkoutservice"},{"callee":"checkoutservice","caller":"frontend"},{"callee":"currencyservice","caller":"frontend"},{"callee":"productcatalogservice","caller":"frontend"},{"callee":"recommendationservice","caller":"frontend"},{"callee":"productcatalogservice","caller":"recommendationservice"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

{"confidence":"high","reason":"Rank emailservice first because emailservice has direct container-memory-failures-total evidence (signed-z 999, persistence 32 bins); although checkoutservice is salient, the caller path checkoutservice -> emailservice means a disturbance in the callee can propagate back toward that caller-side symptom.","services":["emailservice","checkoutservice"]}

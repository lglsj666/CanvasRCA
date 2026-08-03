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
opaque_id: INC-048902022F1A
observation_window={"duration_rel_s":1440.0,"source_metric_rows":1441}
selection_summary={"candidate_count":17,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":258,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["adservice","cartservice","checkoutservice","currencyservice","emailservice","frontend","frontend-external","gke-gke-cluster-default-pool-2e1807ce-0e4z","gke-gke-cluster-default-pool-2e1807ce-cx8g","gke-gke-cluster-default-pool-2e1807ce-w819","gke-gke-cluster-default-pool-2e1807ce-xte3","loadgenerator","paymentservice","productcatalogservice","recommendationservice","redis","shippingservice"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[11.25,33.75,56.25,78.75,101.25,123.75,146.25,168.75,191.25,213.75,236.25,258.75,281.25,303.75,326.25,348.75,371.25,393.75,416.25,438.75,461.25,483.75,506.25,528.75,551.25,573.75,596.25,618.75,641.25,663.75,686.25,708.75,731.25,753.75,776.25,798.75,821.25,843.75,866.25,888.75,911.25,933.75,956.25,978.75,1001.25,1023.75,1046.25,1068.75,1091.25,1113.75,1136.25,1158.75,1181.25,1203.75,1226.25,1248.75,1271.25,1293.75,1316.25,1338.75,1361.25,1383.75,1406.25,1428.75]
[M1] rank=1 service=recommendationservice metric=container-memory-mapped-file baseline=0.0 peak=2318336.0 signed_z=999.0 onset_bin=32 onset_rel_s=731.25 persistence_bins=32
values_compact=rle:0*32,2318336*32
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M2] rank=2 service=recommendationservice metric=istio-latency-90 baseline=0.009608 peak=0.097473 signed_z=999.0 onset_bin=32 onset_rel_s=731.25 persistence_bins=32
values_compact=raw:[0.009626,0.009648,0.009594,0.009544,0.009531,0.009512,0.009515,0.009693,0.009767,0.009617,0.009588,0.009565,0.009534,0.009541,0.009581,0.009652,0.009632,0.009547,0.009543,0.009555,0.009661,0.009782,0.009755,0.009663,0.009654,0.009665,0.009616,0.009562,0.009556,0.009568,0.009572,0.009594,0.009899,0.074926,0.087956,0.089278,0.090534,0.089276,0.095375,0.097369,0.090537,0.090213,0.090918,0.091187,0.089397,0.088125,0.089862,0.090583,0.093132,0.092536,0.091902,0.095065,0.092337,0.089377,0.089465,0.08858,0.08498,0.085438,0.086635,0.090306,0.094583,0.094983,0.091096,0.088183]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M3] rank=3 service=gke-gke-cluster-default-pool-2e1807ce-w819 metric=node-memory-active-bytes baseline=3230.90963 peak=19782041.6 signed_z=999.0 onset_bin=56 onset_rel_s=1271.25 persistence_bins=2
values_compact=delta:2821.688889,91.022222,-546.133333,273.066666,182.044445,-182.044445,-364.088888,546.133333,910.222222,819.2,0,-1274.311111,-91.022222,-182.044445,-364.088889,364.088889,-91.022222,364.088889,546.133333,-91.022222,-819.2,-364.088889,2457.6,273.066667,-2002.488889,0,91.022222,182.044445,-637.155556,-182.044444,455.111111,-455.111111,0,819.2,182.044444,-728.177778,-182.044444,455.111111,364.088889,-637.155556,-364.088889,819.2,455.111112,-728.177778,-637.155556,546.133334,728.177777,-364.088889,-182.044444,182.044444,91.022223,-546.133334,91.022223,91.022222,-273.066667,728.177778,19778309.688889,91.022222,-19778582.755556,-637.155555,91.022222,-182.044444,-91.022223,637.155556
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M4] rank=4 service=recommendationservice metric=istio-latency-50 baseline=0.007416 peak=0.04544 signed_z=690.673 onset_bin=32 onset_rel_s=731.25 persistence_bins=32
values_compact=raw:[0.007395,0.007423,0.007438,0.007404,0.007364,0.007332,0.007347,0.007464,0.007466,0.00738,0.00741,0.007384,0.007299,0.007296,0.007412,0.007445,0.007406,0.007391,0.007379,0.007372,0.007475,0.007542,0.007515,0.007456,0.007438,0.007478,0.007457,0.007392,0.007403,0.007452,0.007449,0.007436,0.007603,0.009537,0.039796,0.041083,0.041452,0.042059,0.043531,0.044745,0.043673,0.043498,0.043656,0.044594,0.042594,0.040676,0.040761,0.041489,0.042971,0.041867,0.040965,0.041552,0.041451,0.041462,0.042209,0.041934,0.039478,0.039693,0.039886,0.041654,0.044225,0.044167,0.043037,0.040299]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M5] rank=5 service=recommendationservice metric=container-sockets baseline=4.0 peak=6.0 signed_z=333.333 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=rle:4*41,6*1,4*22
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M6] rank=6 service=recommendationservice metric=istio-latency-95 baseline=0.010144 peak=0.177547 signed_z=181.277 onset_bin=32 onset_rel_s=731.25 persistence_bins=32
values_compact=raw:[0.009902,0.009927,0.009865,0.009812,0.009802,0.009784,0.009786,0.009971,0.012733,0.009896,0.009861,0.009837,0.009813,0.009821,0.009852,0.009926,0.009911,0.009817,0.009814,0.009828,0.009934,0.013217,0.011819,0.009942,0.009931,0.009937,0.009885,0.009834,0.009825,0.009831,0.009838,0.009864,0.023137,0.090037,0.095438,0.096715,0.09813,0.096493,0.159826,0.176274,0.097186,0.09693,0.097754,0.097729,0.096409,0.095885,0.097785,0.098295,0.1135,0.099991,0.113207,0.147976,0.108333,0.097425,0.096828,0.0959,0.092892,0.093084,0.094352,0.097761,0.129135,0.134444,0.097957,0.095621]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M7] rank=7 service=recommendationservice metric=container-memory-cache baseline=479232.0 peak=2768896.0 signed_z=164.523 onset_bin=32 onset_rel_s=731.25 persistence_bins=32
values_compact=rle:479232*32,2768896*32
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M8] rank=8 service=recommendationservice metric=container-memory-usage-bytes baseline=46822235.022222 peak=53051392.0 signed_z=146.02 onset_bin=32 onset_rel_s=731.25 persistence_bins=32
values_compact=delta:46809088,28672,-4096,-28672,45056,4096,0,-67584,10240,8192,-147456,180224,-24576,4096,-57344,81920,-32768,0,20480,-20480,-94208,16384,69632,69632,-90112,86016,8192,-20480,12288,-8192,12288,-16384,5935104,16384,-45056,-24576,45056,-73728,200704,0,0,8192,-4096,-16384,-20480,20480,-20480,16384,0,0,36864,-16384,32768,-24576,131072,-118784,16384,8192,8192,-28672,-24576,0,-110592,143360
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M9] rank=9 service=recommendationservice metric=container-memory-working-set-bytes baseline=46343003.022222 peak=52572160.0 signed_z=146.02 onset_bin=32 onset_rel_s=731.25 persistence_bins=32
values_compact=delta:46329856,28672,-4096,-28672,45056,4096,0,-67584,10240,8192,-147456,180224,-24576,4096,-57344,81920,-32768,0,20480,-20480,-94208,16384,69632,69632,-90112,86016,8192,-20480,12288,-8192,12288,-16384,5935104,16384,-45056,-24576,45056,-73728,200704,0,0,8192,-4096,-16384,-20480,20480,-20480,16384,0,0,36864,-16384,32768,-24576,131072,-118784,16384,8192,8192,-28672,-24576,0,-110592,143360
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M10] rank=10 service=recommendationservice metric=istio-latency-99 baseline=0.018895 peak=0.49125 signed_z=126.037 onset_bin=32 onset_rel_s=731.25 persistence_bins=32
values_compact=raw:[0.020436,0.020936,0.019034,0.015012,0.013845,0.010467,0.010817,0.023842,0.024147,0.020228,0.018857,0.017562,0.015904,0.01675,0.018416,0.024191,0.024427,0.01615,0.015432,0.0169,0.022564,0.024795,0.023385,0.021205,0.021007,0.0211,0.019786,0.017247,0.01638,0.016675,0.017262,0.021047,0.0921,0.161929,0.173125,0.196261,0.21015,0.191643,0.365781,0.37,0.19798,0.19475,0.205321,0.204056,0.1885,0.186143,0.208364,0.211485,0.489167,0.48125,0.222641,0.229595,0.221667,0.205879,0.196818,0.181794,0.099221,0.099201,0.138045,0.210946,0.230442,0.229111,0.207276,0.177029]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M11] rank=11 service=checkoutservice metric=istio-latency-95 baseline=0.233161 peak=1.1125 signed_z=117.08 onset_bin=38 onset_rel_s=866.25 persistence_bins=3
values_compact=raw:[0.245714,0.234318,0.231667,0.234167,0.230714,0.23125,0.232083,0.245714,0.246625,0.235,0.232,0.2335,0.237647,0.237308,0.2375,0.237045,0.23625,0.2365,0.234375,0.225833,0.215909,0.236,0.2445,0.2375,0.233056,0.224615,0.225156,0.229079,0.229,0.224,0.224688,0.225625,0.230312,0.230962,0.213571,0.22,0.231786,0.235,1.1125,1.0375,0.235326,0.235326,0.233816,0.230714,0.228571,0.227895,0.223553,0.213864,0.222727,0.231471,0.237727,0.2365,0.233393,0.234063,0.230179,0.229375,0.234531,0.2413,0.244643,0.235,0.234531,0.249118,0.237045,0.13]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M12] rank=12 service=recommendationservice metric=container-memory-failures-total baseline=7.01424 peak=166.317502 signed_z=80.412 onset_bin=32 onset_rel_s=731.25 persistence_bins=2
values_compact=raw:[8.118308,8.468052,11.20774,10.44329,5.83209,6.299192,7.45557,9.479327,11.952092,6.98812,5.093577,5.867461,7.153406,7.145195,6.211711,5.376228,8.660398,3.12565,5.569026,6.837581,8.482342,9.056794,6.937266,3.821126,6.216755,7.339386,7.740234,8.317416,7.956366,4.806057,3.849375,5.364259,110.5394,133.286615,6.915888,6.825397,6.521789,7.605782,7.774284,8.040071,9.088167,9.17685,7.832557,6.198478,8.361246,5.719235,6.633637,6.646783,5.417792,6.922781,5.5911,6.417173,7.186274,7.415694,7.702455,7.373606,6.480541,5.524107,7.081195,6.575831,6.983785,7.935352,6.263048,4.86417]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[699.0,1440.0]

=== LOG SUMMARY ===
{"entries":[{"change_pct":-7.9,"n_during":978,"n_pre":1062,"service":"checkoutservice"},{"change_pct":-7.9,"n_during":326,"n_pre":354,"service":"emailservice"},{"change_pct":-7.9,"n_during":652,"n_pre":708,"service":"paymentservice"},{"change_pct":6.3,"n_during":5569,"n_pre":5237,"service":"adservice"},{"change_pct":4.3,"n_during":32733,"n_pre":31381,"service":"frontend"},{"change_pct":4.2,"n_during":29367,"n_pre":28173,"service":"currencyservice"},{"change_pct":-3.1,"n_during":5354,"n_pre":5524,"service":"shippingservice"},{"change_pct":2.8,"n_during":6870,"n_pre":6680,"service":"recommendationservice"}],"mode":"volume","omitted_services":2,"service_count":10}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":1606.8,"error_pct":0.0,"p95_during_ms":82.729,"p95_pre_ms":4.847099999999999,"service":"recommendationservice","spans":27676},{"delta_pct":53.6,"error_pct":0.0,"p95_during_ms":89.8775,"p95_pre_ms":58.49734999999996,"service":"frontend","spans":209188},{"delta_pct":-27.9,"error_pct":0.0,"p95_during_ms":0.37634999999999996,"p95_pre_ms":0.5221999999999997,"service":"paymentservice","spans":968},{"delta_pct":-10.5,"error_pct":0.0,"p95_during_ms":63.828749999999985,"p95_pre_ms":71.28374999999998,"service":"checkoutservice","spans":9312},{"delta_pct":10.4,"error_pct":0.0,"p95_during_ms":0.44374999999999964,"p95_pre_ms":0.402,"service":"emailservice","spans":1256},{"delta_pct":8.0,"error_pct":0.0,"p95_during_ms":0.027,"p95_pre_ms":0.025,"service":"productcatalogservice","spans":104071},{"delta_pct":-0.9,"error_pct":0.0,"p95_during_ms":0.213,"p95_pre_ms":0.215,"service":"currencyservice","spans":57824}],"omitted_services":0,"service_count":7}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=3 omitted_edges=1
[{"evidence_source":"trace","onset_rel_s":735.0,"rank":1,"service":"recommendationservice","severity_z":200.876},{"evidence_source":"trace","onset_rel_s":735.0,"rank":2,"service":"frontend","severity_z":7.143},{"evidence_source":"metric","onset_rel_s":811.8,"rank":3,"service":"shippingservice","severity_z":41.235},{"evidence_source":"metric","onset_rel_s":862.2,"rank":4,"service":"checkoutservice","severity_z":117.08},{"evidence_source":"metric","onset_rel_s":1129.2,"rank":5,"service":"adservice","severity_z":13.834},{"evidence_source":"metric","onset_rel_s":1197.0,"rank":6,"service":"paymentservice","severity_z":50.454},{"evidence_source":"metric","onset_rel_s":1210.2,"rank":7,"service":"redis","severity_z":25.759},{"evidence_source":"metric","onset_rel_s":1243.8,"rank":8,"service":"gke-gke-cluster-default-pool-2e1807ce-cx8g","severity_z":39.797},{"evidence_source":"metric","onset_rel_s":1267.8,"rank":9,"service":"gke-gke-cluster-default-pool-2e1807ce-w819","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1428.0,"rank":10,"service":"emailservice","severity_z":51.865},{"evidence_source":"none","onset_rel_s":null,"rank":11,"service":"productcatalogservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":12,"service":"currencyservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":13,"service":"cartservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":14,"service":"gke-gke-cluster-default-pool-2e1807ce-0e4z","severity_z":0.0}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"currencyservice","caller":"checkoutservice"},{"callee":"emailservice","caller":"checkoutservice"},{"callee":"paymentservice","caller":"checkoutservice"},{"callee":"productcatalogservice","caller":"checkoutservice"},{"callee":"checkoutservice","caller":"frontend"},{"callee":"currencyservice","caller":"frontend"},{"callee":"productcatalogservice","caller":"frontend"},{"callee":"recommendationservice","caller":"frontend"},{"callee":"productcatalogservice","caller":"recommendationservice"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

{"confidence":"high","reason":"Rank recommendationservice first because recommendationservice has direct container-memory-mapped-file evidence (signed-z 999, persistence 32 bins); although frontend is salient, the caller path frontend -> recommendationservice means a disturbance in the callee can propagate back toward that caller-side symptom.","services":["recommendationservice","frontend"]}

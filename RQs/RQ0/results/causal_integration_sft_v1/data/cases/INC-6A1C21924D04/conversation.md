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
opaque_id: INC-6A1C21924D04
observation_window={"duration_rel_s":1440.0,"source_metric_rows":1441}
selection_summary={"candidate_count":17,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":263,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["adservice","cartservice","checkoutservice","currencyservice","emailservice","frontend","frontend-external","gke-gke-cluster-default-pool-2e1807ce-0e4z","gke-gke-cluster-default-pool-2e1807ce-cx8g","gke-gke-cluster-default-pool-2e1807ce-w819","gke-gke-cluster-default-pool-2e1807ce-xte3","loadgenerator","paymentservice","productcatalogservice","recommendationservice","redis","shippingservice"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[11.25,33.75,56.25,78.75,101.25,123.75,146.25,168.75,191.25,213.75,236.25,258.75,281.25,303.75,326.25,348.75,371.25,393.75,416.25,438.75,461.25,483.75,506.25,528.75,551.25,573.75,596.25,618.75,641.25,663.75,686.25,708.75,731.25,753.75,776.25,798.75,821.25,843.75,866.25,888.75,911.25,933.75,956.25,978.75,1001.25,1023.75,1046.25,1068.75,1091.25,1113.75,1136.25,1158.75,1181.25,1203.75,1226.25,1248.75,1271.25,1293.75,1316.25,1338.75,1361.25,1383.75,1406.25,1428.75]
[M1] rank=1 service=currencyservice metric=container-memory-mapped-file baseline=0.0 peak=2211840.0 signed_z=999.0 onset_bin=32 onset_rel_s=731.25 persistence_bins=32
values_compact=rle:0*32,2211840*32
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M2] rank=2 service=currencyservice metric=istio-latency-99 baseline=0.095601 peak=1.550294 signed_z=999.0 onset_bin=32 onset_rel_s=731.25 persistence_bins=32
values_compact=raw:[0.095348,0.096602,0.096489,0.095193,0.095603,0.095656,0.09532,0.095536,0.094577,0.096219,0.096458,0.095462,0.094664,0.093542,0.095168,0.095804,0.095364,0.094874,0.094366,0.095693,0.096587,0.096473,0.096922,0.095887,0.096432,0.09634,0.095527,0.095652,0.094382,0.095599,0.095822,0.09474,0.278611,0.878619,0.95327,0.953125,0.946899,0.943652,0.958655,0.960252,0.947491,0.945056,0.955852,0.955348,0.950047,0.94987,0.960147,0.962512,0.953777,0.951153,1.106324,1.466,1.043928,0.986769,0.954109,0.960734,0.973774,0.962368,0.942482,0.937589,0.937134,0.943358,0.963367,0.971606]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M3] rank=3 service=productcatalogservice metric=istio-latency-99 baseline=0.004954 peak=0.016426 signed_z=913.354 onset_bin=34 onset_rel_s=776.25 persistence_bins=30
values_compact=raw:[0.004962,0.004961,0.004954,0.004945,0.004971,0.004971,0.004955,0.004959,0.004942,0.00494,0.004947,0.004977,0.004969,0.00494,0.004955,0.004952,0.004941,0.004942,0.004943,0.004942,0.004945,0.004951,0.004984,0.004979,0.004944,0.004948,0.004949,0.004946,0.004951,0.004962,0.00495,0.004944,0.004952,0.004975,0.00802,0.012705,0.007497,0.006628,0.009046,0.009081,0.008169,0.008354,0.008218,0.007284,0.008429,0.009196,0.009001,0.009106,0.008122,0.006535,0.008513,0.009283,0.007073,0.005395,0.00758,0.007216,0.009585,0.016401,0.009257,0.008355,0.007813,0.007925,0.009831,0.009858]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M4] rank=4 service=currencyservice metric=container-memory-working-set-bytes baseline=45786032.355556 peak=268439552.0 signed_z=823.551 onset_bin=32 onset_rel_s=731.25 persistence_bins=32
values_compact=delta:46022656,-208896,61440,393216,-544768,94208,-217088,0,524288,-577536,24576,-53248,143360,159744,-450560,524288,-581632,114688,180224,-294912,376832,-102400,139264,598016,-589824,397312,180224,-581632,413696,-444416,38912,425984,96776192,85475328,-103755776,15667200,22908928,105193472,4096,-74649600,71622656,-109295616,112318464,-4096,-104554496,104562688,-189222912,185188352,-216625152,129241088,51699712,39714816,-127012864,7938048,-70537216,31080448,36671488,-87908352,209772544,-16384,16384,-39735296,39735296,-135393280
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M5] rank=5 service=currencyservice metric=container-memory-usage-bytes baseline=45826992.355556 peak=268439552.0 signed_z=823.399 onset_bin=32 onset_rel_s=731.25 persistence_bins=32
values_compact=delta:46063616,-208896,61440,393216,-544768,94208,-217088,0,524288,-577536,24576,-53248,143360,159744,-450560,524288,-581632,114688,180224,-294912,376832,-102400,139264,598016,-589824,397312,180224,-581632,413696,-444416,38912,425984,96735232,85475328,-103755776,15667200,22908928,105193472,4096,-74649600,71622656,-109295616,112318464,-4096,-104554496,104562688,-189222912,185188352,-216625152,129241088,51699712,39714816,-127012864,7938048,-70537216,31080448,36671488,-87908352,209772544,-16384,16384,-39735296,39735296,-135393280
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M6] rank=6 service=currencyservice metric=container-memory-rss baseline=42238168.177778 peak=263372800.0 signed_z=816.61 onset_bin=32 onset_rel_s=731.25 persistence_bins=31
values_compact=delta:42532864,-399360,178176,348160,-692224,364544,-348160,0,659456,-692224,135168,-200704,159744,290816,-454656,401408,-458752,110592,184320,-294912,380928,-114688,131072,610304,-602112,274432,311296,-585728,425984,-491520,81920,299008,95539200,85319680,-103563264,15085568,23257088,105119744,16384,-74678272,71667712,-109099008,112121856,-4096,-104550400,104546304,-188985344,184971264,-216752128,129425408,13205504,78139392,-126758912,7589888,-70057984,31006720,36601856,-87707648,209371136,-40960,12288,-39702528,39694336,-135127040
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M7] rank=7 service=currencyservice metric=container-memory-failures-total baseline=400.53158 peak=62733.529812 signed_z=677.998 onset_bin=32 onset_rel_s=731.25 persistence_bins=32
values_compact=delta:380.570714,121.092717,134.630138,-192.29895,-101.345467,58.682673,-8.704307,-35.684837,-9.901275,18.303831,0,-25.160784,2.574189,17.002379,22.474171,-10.450735,-17.312544,15.119746,-5.57469,40.769423,216.098939,1.74052,-215.635246,-7.512953,46.824394,-10.116387,-60.767358,0,-1.543177,-6.724842,-58.252419,62.912723,8364.294415,23665.636118,17832.579794,9920.423015,1764.147318,814.638566,-1601.32538,-717.93427,321.940643,-309.63149,-501.6841,324.714843,-768.855819,715.951058,-386.400024,48.887634,-1234.125667,262.127942,1229.879142,2076.927698,-2736.823839,0,344.812612,317.253597,-155.089753,-991.182874,902.637828,294.13102,403.753172,-273.107462,-321.740993,-123.036845
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M8] rank=8 service=currencyservice metric=istio-latency-50 baseline=0.004114 peak=0.08386 signed_z=501.227 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=raw:[0.004447,0.004467,0.004405,0.004281,0.004052,0.00397,0.003967,0.004077,0.004064,0.004145,0.004158,0.004209,0.004078,0.003842,0.004024,0.004275,0.004157,0.004002,0.003997,0.004092,0.004277,0.004332,0.004242,0.004023,0.003942,0.003917,0.004066,0.004189,0.003973,0.003999,0.003977,0.003986,0.004458,0.008878,0.076152,0.076574,0.074869,0.076102,0.078061,0.079064,0.075706,0.074137,0.076985,0.076944,0.077338,0.075953,0.07609,0.079007,0.080668,0.07949,0.080662,0.081616,0.080628,0.079667,0.075979,0.076188,0.078871,0.079723,0.078697,0.076325,0.075802,0.076506,0.079331,0.080149]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M9] rank=9 service=currencyservice metric=container-memory-cache baseline=40960.0 peak=2211840.0 signed_z=339.862 onset_bin=32 onset_rel_s=731.25 persistence_bins=32
values_compact=rle:40960*32,2211840*32
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M10] rank=10 service=currencyservice metric=istio-latency-95 baseline=0.075503 peak=0.826336 signed_z=276.721 onset_bin=32 onset_rel_s=731.25 persistence_bins=32
values_compact=raw:[0.075585,0.079012,0.079504,0.0758,0.074779,0.074909,0.074138,0.075362,0.072886,0.07639,0.078056,0.076183,0.071954,0.06771,0.074682,0.07807,0.074556,0.071722,0.071832,0.073542,0.079133,0.079407,0.078564,0.076403,0.078341,0.077583,0.076562,0.077264,0.071912,0.074547,0.075693,0.0737,0.090271,0.367361,0.724827,0.725084,0.733509,0.718258,0.738103,0.751808,0.723519,0.7103,0.738036,0.737003,0.750237,0.749349,0.727952,0.74835,0.766396,0.755764,0.79285,0.820098,0.76599,0.754161,0.750743,0.749061,0.780818,0.77469,0.712408,0.687945,0.685672,0.71679,0.781818,0.772401]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M11] rank=11 service=checkoutservice metric=istio-latency-90 baseline=0.228485 peak=2.185714 signed_z=162.265 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=raw:[0.24175,0.235,0.232692,0.228478,0.229091,0.235937,0.2275,0.2146,0.22625,0.28125,0.23875,0.22375,0.22375,0.218929,0.218333,0.230714,0.229474,0.2185,0.22,0.22,0.2175,0.221429,0.226964,0.22625,0.223261,0.230227,0.244231,0.244,0.224737,0.223529,0.226094,0.221452,0.217,1.225,2.125,2.168421,1.996429,1.621429,1.88125,2.05,1.6375,1.1125,1.95625,2.05,1.985714,1.96,2.125,2.129412,2.026923,2.10625,2.103571,1.980769,2.10625,2.106224,2.05,2.0,2.005,1.621429,0.9,1.84,1.9,1.75,1.54,1.855]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M12] rank=12 service=adservice metric=istio-latency-99 baseline=0.005117 peak=0.073417 signed_z=156.502 onset_bin=36 onset_rel_s=821.25 persistence_bins=24
values_compact=raw:[0.004972,0.004984,0.004985,0.004978,0.006211,0.005881,0.004966,0.004984,0.00499,0.004971,0.004966,0.004979,0.004984,0.004972,0.00496,0.004965,0.004977,0.004972,0.00496,0.00496,0.00496,0.004978,0.006845,0.005669,0.004971,0.004977,0.004989,0.004995,0.004977,0.004966,0.004972,0.004984,0.004978,0.006285,0.005865,0.006239,0.057998,0.0094,0.009165,0.00993,0.048375,0.009807,0.00865,0.00936,0.009417,0.008515,0.007783,0.0077,0.0674,0.073167,0.009033,0.005967,0.004979,0.007867,0.008504,0.008154,0.008841,0.008947,0.009613,0.009772,0.005617,0.004988,0.007606,0.00845]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[704.0,1440.0]

=== LOG SUMMARY ===
{"entries":[{"error_logs":45,"error_pct":0.07,"service":"frontend","total_logs":60490}],"mode":"errors","omitted_services":9,"service_count":10}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":827.9,"error_pct":0.0,"p95_during_ms":649.9574500000001,"p95_pre_ms":70.04864999999997,"service":"frontend","spans":196240},{"delta_pct":402.7,"error_pct":0.0,"p95_during_ms":405.87059999999985,"p95_pre_ms":80.74069999999992,"service":"checkoutservice","spans":8828},{"delta_pct":61.3,"error_pct":0.0,"p95_during_ms":7.5230999999999915,"p95_pre_ms":4.665449999999999,"service":"recommendationservice","spans":26086},{"delta_pct":-6.6,"error_pct":0.0,"p95_during_ms":0.239,"p95_pre_ms":0.256,"service":"currencyservice","spans":54070},{"delta_pct":-5.6,"error_pct":0.0,"p95_during_ms":0.3959499999999998,"p95_pre_ms":0.4196,"service":"paymentservice","spans":933},{"delta_pct":3.2,"error_pct":0.0,"p95_during_ms":0.44354999999999994,"p95_pre_ms":0.43,"service":"emailservice","spans":1221},{"delta_pct":0.0,"error_pct":0.0,"p95_during_ms":0.024,"p95_pre_ms":0.024,"service":"productcatalogservice","spans":97676}],"omitted_services":0,"service_count":7}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=3 omitted_edges=2
[{"evidence_source":"metric","onset_rel_s":727.8,"rank":1,"service":"currencyservice","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":733.8,"rank":2,"service":"gke-gke-cluster-default-pool-2e1807ce-xte3","severity_z":38.558},{"evidence_source":"trace","onset_rel_s":735.0,"rank":3,"service":"checkoutservice","severity_z":111.964},{"evidence_source":"trace","onset_rel_s":735.0,"rank":4,"service":"recommendationservice","severity_z":10.457},{"evidence_source":"trace","onset_rel_s":735.0,"rank":5,"service":"frontend","severity_z":111.707},{"evidence_source":"metric","onset_rel_s":736.8,"rank":6,"service":"emailservice","severity_z":54.721},{"evidence_source":"metric","onset_rel_s":750.0,"rank":7,"service":"gke-gke-cluster-default-pool-2e1807ce-cx8g","severity_z":85.505},{"evidence_source":"metric","onset_rel_s":759.0,"rank":8,"service":"cartservice","severity_z":33.392},{"evidence_source":"metric","onset_rel_s":789.0,"rank":9,"service":"productcatalogservice","severity_z":913.354},{"evidence_source":"metric","onset_rel_s":819.0,"rank":10,"service":"adservice","severity_z":156.502},{"evidence_source":"metric","onset_rel_s":969.0,"rank":11,"service":"shippingservice","severity_z":119.714},{"evidence_source":"metric","onset_rel_s":982.2,"rank":12,"service":"redis","severity_z":12.341},{"evidence_source":"trace","onset_rel_s":1065.0,"rank":13,"service":"paymentservice","severity_z":13.978},{"evidence_source":"metric","onset_rel_s":1078.2,"rank":14,"service":"gke-gke-cluster-default-pool-2e1807ce-0e4z","severity_z":19.021}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"currencyservice","caller":"checkoutservice"},{"callee":"emailservice","caller":"checkoutservice"},{"callee":"paymentservice","caller":"checkoutservice"},{"callee":"productcatalogservice","caller":"checkoutservice"},{"callee":"checkoutservice","caller":"frontend"},{"callee":"currencyservice","caller":"frontend"},{"callee":"productcatalogservice","caller":"frontend"},{"callee":"recommendationservice","caller":"frontend"},{"callee":"productcatalogservice","caller":"recommendationservice"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

{"confidence":"high","reason":"Rank currencyservice first because currencyservice has direct container-memory-mapped-file evidence (signed-z 999, persistence 32 bins); although checkoutservice is salient, the caller path checkoutservice -> currencyservice means a disturbance in the callee can propagate back toward that caller-side symptom.","services":["currencyservice","checkoutservice"]}

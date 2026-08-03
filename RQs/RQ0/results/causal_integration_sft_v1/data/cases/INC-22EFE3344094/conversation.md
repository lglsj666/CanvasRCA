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
opaque_id: INC-22EFE3344094
observation_window={"duration_rel_s":1440.0,"source_metric_rows":1441}
selection_summary={"candidate_count":17,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":271,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["adservice","cartservice","checkoutservice","currencyservice","emailservice","frontend","frontend-external","gke-gke-cluster-default-pool-2e1807ce-0e4z","gke-gke-cluster-default-pool-2e1807ce-cx8g","gke-gke-cluster-default-pool-2e1807ce-w819","gke-gke-cluster-default-pool-2e1807ce-xte3","loadgenerator","paymentservice","productcatalogservice","recommendationservice","redis","shippingservice"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[11.25,33.75,56.25,78.75,101.25,123.75,146.25,168.75,191.25,213.75,236.25,258.75,281.25,303.75,326.25,348.75,371.25,393.75,416.25,438.75,461.25,483.75,506.25,528.75,551.25,573.75,596.25,618.75,641.25,663.75,686.25,708.75,731.25,753.75,776.25,798.75,821.25,843.75,866.25,888.75,911.25,933.75,956.25,978.75,1001.25,1023.75,1046.25,1068.75,1091.25,1113.75,1136.25,1158.75,1181.25,1203.75,1226.25,1248.75,1271.25,1293.75,1316.25,1338.75,1361.25,1383.75,1406.25,1428.75]
[M1] rank=1 service=productcatalogservice metric=istio-latency-50 baseline=0.001786 peak=0.103491 signed_z=999.0 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=delta:0.001911,-0.000004,0.000038,-0.000016,-0.000065,-0.000031,0.000023,-0.00006,-0.000038,0.00001,-0.000017,0.000002,0,0,0.000076,-0.000008,-0.000057,0.000023,-0.000038,-0.000048,0.000021,-0.000034,0.000046,0.000013,-0.00004,0.000018,-0.000011,0.000084,0.00002,-0.000085,0.000001,0.000038,0.000012,0.00087,0.001516,0.096939,-0.096152,0.000018,0.096119,-0.000972,-0.095134,0.000001,0.095217,0.00061,-0.095866,0.000033,0.095435,0.000265,-0.095715,0.000007,0.09677,-0.001172,-0.095624,0.00004,0.095587,0.000049,-0.095664,0.000023,0.095757,-0.00025,0,-0.095495,-0.000002,0
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M2] rank=2 service=recommendationservice metric=istio-latency-50 baseline=0.007478 peak=0.175487 signed_z=999.0 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=delta:0.007634,-0.000123,-0.000046,0.000017,0.000037,-0.000028,-0.000007,-0.000002,-0.000004,-0.000013,-0.000009,0.000012,0.000016,0,0.000039,0.000069,-0.000016,-0.000081,-0.00001,0.000004,-0.000034,-0.000035,0.000052,-0.000002,-0.00004,-0.000016,-0.000005,0.000022,0.000015,-0.000006,-0.000009,0.000026,0.000021,0.05809,0.104313,0.005119,0,0,0,0,0,0,0,0.000234,0.000001,-0.000235,0,0,0,0,0,0,0.000232,0.000002,-0.000234,0,0.000477,0.000001,-0.000478,0,0,0,0.000237,0
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M3] rank=3 service=productcatalogservice metric=istio-latency-90 baseline=0.004373 peak=0.220698 signed_z=999.0 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=raw:[0.004405,0.004399,0.004408,0.004407,0.004391,0.004383,0.004392,0.004377,0.004364,0.004365,0.00436,0.004359,0.004358,0.004365,0.00439,0.004392,0.004383,0.00438,0.004364,0.004354,0.004357,0.004352,0.004359,0.004363,0.004354,0.004357,0.004356,0.004371,0.004378,0.00436,0.004358,0.004364,0.004378,0.189178,0.216215,0.220222,0.219819,0.219872,0.220219,0.220024,0.219877,0.219911,0.220041,0.220163,0.219782,0.219912,0.220084,0.220137,0.219869,0.219902,0.220349,0.220115,0.219783,0.219985,0.220164,0.220125,0.21982,0.219904,0.220148,0.220098,0.220098,0.219933,0.219987,0.220025]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M4] rank=4 service=recommendationservice metric=istio-latency-90 baseline=0.009599 peak=0.235877 signed_z=999.0 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=delta:0.009802,-0.000184,-0.000056,0.000034,0.000007,0.000002,-0.000004,-0.000022,-0.000004,-0.000021,-0.000002,0.000005,-0.000019,0.000001,0.000132,0.000112,-0.000056,-0.00009,-0.000016,0.00003,-0.000001,-0.000062,0.000026,-0.000035,-0.000045,-0.00001,0.00001,0.000013,-0.000002,-0.000004,-0.000004,0.000067,0.000064,0.208944,0.015364,0.001024,0,0,0,0,0,0,0,0.000421,0.000003,-0.000424,0,0,0,0,0,0,0.000417,0.000004,-0.000421,0,0.000859,0.000002,-0.000861,0,0,0,0.000426,0
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M5] rank=5 service=productcatalogservice metric=istio-latency-95 baseline=0.004696 peak=0.235349 signed_z=999.0 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=raw:[0.004717,0.004711,0.004716,0.004715,0.004707,0.004701,0.004709,0.004699,0.00469,0.00469,0.004686,0.004684,0.004683,0.00469,0.004709,0.004713,0.00471,0.004704,0.004691,0.004686,0.004687,0.004685,0.004687,0.004691,0.004685,0.004686,0.004687,0.004692,0.004697,0.004689,0.004686,0.004691,0.004702,0.219589,0.233108,0.235111,0.234909,0.234936,0.235109,0.235012,0.234939,0.234956,0.235021,0.235082,0.234891,0.234956,0.235042,0.235068,0.234935,0.234951,0.235174,0.235057,0.234922,0.235023,0.235112,0.235062,0.23491,0.234952,0.235074,0.235049,0.235049,0.234966,0.235025,0.235043]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M6] rank=6 service=productcatalogservice metric=istio-latency-99 baseline=0.004955 peak=0.247091 signed_z=999.0 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=raw:[0.004968,0.00496,0.00496,0.004961,0.00496,0.004956,0.004963,0.004958,0.004951,0.00495,0.004947,0.004946,0.004943,0.004951,0.004962,0.00497,0.004973,0.004964,0.004955,0.004951,0.004952,0.004951,0.00495,0.004953,0.00495,0.00495,0.004951,0.004951,0.004952,0.00495,0.004949,0.004951,0.004962,0.243918,0.246622,0.247022,0.246982,0.246987,0.247022,0.247002,0.246988,0.246991,0.247004,0.247016,0.246978,0.246991,0.247008,0.247014,0.246987,0.24699,0.247035,0.247011,0.247033,0.247054,0.247024,0.247012,0.246982,0.24699,0.247015,0.24701,0.24701,0.246993,0.247056,0.247058]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M7] rank=7 service=frontend metric=istio-latency-50 baseline=0.055101 peak=1.505507 signed_z=360.868 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=raw:[0.04813,0.057824,0.064646,0.061633,0.056627,0.057333,0.058765,0.054248,0.055724,0.05489,0.055357,0.055035,0.052321,0.056134,0.062835,0.062062,0.054818,0.050187,0.049289,0.056076,0.05681,0.049167,0.049386,0.050182,0.049936,0.050282,0.055656,0.058433,0.055116,0.052298,0.050804,0.057155,0.060115,0.195,1.296875,1.437017,1.423222,1.445652,1.476676,1.477377,1.454899,1.465596,1.47561,1.434646,1.415348,1.425234,1.417808,1.412669,1.442217,1.47401,1.444836,1.456997,1.447948,1.432203,1.474537,1.470904,1.451172,1.4644,1.466154,1.484444,1.505507,1.476852,1.437701,1.420906]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M8] rank=8 service=recommendationservice metric=istio-latency-95 baseline=0.010004 peak=0.243425 signed_z=343.489 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=delta:0.013194,-0.003313,-0.000057,0.000036,0.000004,0.000004,-0.000003,-0.000024,-0.000004,-0.000022,0,0.000003,-0.000024,0.000004,0.000142,0.002848,-0.002792,-0.000091,-0.000017,0.000035,-0.000001,-0.000064,0.000025,-0.00004,-0.000046,-0.00001,0.000012,0.000013,-0.000004,-0.000004,-0.000003,0.000071,0.000069,0.224365,0.007682,0.000512,0,0,0,0,0,0,0,0.000444,0.000003,-0.000447,0,0,0,0,0,0,0.00044,0.000005,-0.000445,0,0.000906,0.000002,-0.000908,0,0,0,0.00045,0
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M9] rank=9 service=currencyservice metric=container-sockets baseline=4.0 peak=3.0 signed_z=-250.0 onset_bin=42 onset_rel_s=956.25 persistence_bins=22
values_compact=rle:4*42,3*22
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M10] rank=10 service=shippingservice metric=container-sockets baseline=4.0 peak=3.0 signed_z=-250.0 onset_bin=41 onset_rel_s=933.75 persistence_bins=23
values_compact=rle:4*41,3*23
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M11] rank=11 service=frontend metric=istio-latency-90 baseline=0.214008 peak=2.302837 signed_z=212.237 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=raw:[0.209561,0.221254,0.220504,0.223988,0.218466,0.213239,0.213255,0.205,0.20798,0.2022,0.205052,0.215326,0.211324,0.215769,0.240065,0.24614,0.221755,0.211689,0.206465,0.217948,0.218555,0.201124,0.209466,0.21523,0.213209,0.205049,0.198112,0.20855,0.211646,0.210354,0.209389,0.215198,0.220147,2.081994,2.263542,2.291113,2.284644,2.292609,2.298834,2.302837,2.298445,2.296789,2.302439,2.294488,2.286867,2.285047,2.283562,2.282534,2.288443,2.294802,2.292723,2.294898,2.28959,2.286441,2.294907,2.294181,2.290234,2.29288,2.293231,2.296889,2.301101,2.29537,2.28754,2.287997]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M12] rank=12 service=adservice metric=container-sockets baseline=4.0 peak=5.0 signed_z=200.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=rle:4*41,5*1,4*22
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[724.0,1440.0]

=== LOG SUMMARY ===
{"entries":[{"change_pct":-33.3,"n_during":10,"n_pre":15,"service":"redis"},{"change_pct":-32.4,"n_during":714,"n_pre":1056,"service":"checkoutservice"},{"change_pct":-32.4,"n_during":238,"n_pre":352,"service":"emailservice"},{"change_pct":-32.4,"n_during":476,"n_pre":704,"service":"paymentservice"},{"change_pct":-27.4,"n_during":4056,"n_pre":5590,"service":"shippingservice"},{"change_pct":-24.5,"n_during":7120,"n_pre":9430,"service":"cartservice"},{"change_pct":-24.5,"n_during":22114,"n_pre":29298,"service":"currencyservice"},{"change_pct":-24.3,"n_during":24769,"n_pre":32729,"service":"frontend"}],"mode":"volume","omitted_services":2,"service_count":10}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":3842.3,"error_pct":0.0,"p95_during_ms":205.07655,"p95_pre_ms":5.202,"service":"recommendationservice","spans":24598},{"delta_pct":1743.6,"error_pct":0.0,"p95_during_ms":1443.006,"p95_pre_ms":78.27019999999996,"service":"frontend","spans":186083},{"delta_pct":206.1,"error_pct":0.0,"p95_during_ms":296.1649999999995,"p95_pre_ms":96.749,"service":"checkoutservice","spans":8290},{"delta_pct":32.0,"error_pct":0.0,"p95_during_ms":0.033,"p95_pre_ms":0.025,"service":"productcatalogservice","spans":92309},{"delta_pct":16.4,"error_pct":0.0,"p95_during_ms":0.4700500000000002,"p95_pre_ms":0.4037499999999999,"service":"paymentservice","spans":878},{"delta_pct":13.2,"error_pct":0.0,"p95_during_ms":0.41639999999999916,"p95_pre_ms":0.36779999999999974,"service":"emailservice","spans":1166},{"delta_pct":5.9,"error_pct":0.0,"p95_during_ms":0.216,"p95_pre_ms":0.204,"service":"currencyservice","spans":51699}],"omitted_services":0,"service_count":7}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=3 omitted_edges=2
[{"evidence_source":"metric","onset_rel_s":732.0,"rank":1,"service":"gke-gke-cluster-default-pool-2e1807ce-cx8g","severity_z":31.263},{"evidence_source":"trace","onset_rel_s":735.0,"rank":2,"service":"recommendationservice","severity_z":391.82},{"evidence_source":"trace","onset_rel_s":735.0,"rank":3,"service":"frontend","severity_z":177.343},{"evidence_source":"trace","onset_rel_s":735.0,"rank":4,"service":"checkoutservice","severity_z":35.5},{"evidence_source":"metric","onset_rel_s":853.2,"rank":5,"service":"gke-gke-cluster-default-pool-2e1807ce-0e4z","severity_z":14.41},{"evidence_source":"metric","onset_rel_s":889.2,"rank":6,"service":"emailservice","severity_z":51.915},{"evidence_source":"metric","onset_rel_s":916.8,"rank":7,"service":"adservice","severity_z":200.0},{"evidence_source":"metric","onset_rel_s":928.8,"rank":8,"service":"shippingservice","severity_z":250.0},{"evidence_source":"metric","onset_rel_s":940.8,"rank":9,"service":"currencyservice","severity_z":250.0},{"evidence_source":"metric","onset_rel_s":1051.2,"rank":10,"service":"cartservice","severity_z":56.055},{"evidence_source":"trace","onset_rel_s":1125.0,"rank":11,"service":"productcatalogservice","severity_z":4.358},{"evidence_source":"metric","onset_rel_s":1126.8,"rank":12,"service":"paymentservice","severity_z":58.521},{"evidence_source":"metric","onset_rel_s":1233.0,"rank":13,"service":"redis","severity_z":25.494},{"evidence_source":"none","onset_rel_s":null,"rank":14,"service":"gke-gke-cluster-default-pool-2e1807ce-w819","severity_z":0.0}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"currencyservice","caller":"checkoutservice"},{"callee":"emailservice","caller":"checkoutservice"},{"callee":"paymentservice","caller":"checkoutservice"},{"callee":"productcatalogservice","caller":"checkoutservice"},{"callee":"checkoutservice","caller":"frontend"},{"callee":"currencyservice","caller":"frontend"},{"callee":"productcatalogservice","caller":"frontend"},{"callee":"recommendationservice","caller":"frontend"},{"callee":"productcatalogservice","caller":"recommendationservice"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

{"confidence":"high","reason":"Rank productcatalogservice first because productcatalogservice has direct istio-latency-50 evidence (signed-z 999, persistence 31 bins); although recommendationservice is salient, the caller path recommendationservice -> productcatalogservice means a disturbance in the callee can propagate back toward that caller-side symptom.","services":["productcatalogservice","recommendationservice"]}

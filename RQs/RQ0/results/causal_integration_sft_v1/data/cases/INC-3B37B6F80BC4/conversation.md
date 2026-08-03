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
opaque_id: INC-3B37B6F80BC4
observation_window={"duration_rel_s":1440.0,"source_metric_rows":1441}
selection_summary={"candidate_count":17,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":267,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["adservice","cartservice","checkoutservice","currencyservice","emailservice","frontend","frontend-external","gke-gke-cluster-default-pool-2e1807ce-0e4z","gke-gke-cluster-default-pool-2e1807ce-cx8g","gke-gke-cluster-default-pool-2e1807ce-w819","gke-gke-cluster-default-pool-2e1807ce-xte3","loadgenerator","paymentservice","productcatalogservice","recommendationservice","redis","shippingservice"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[11.25,33.75,56.25,78.75,101.25,123.75,146.25,168.75,191.25,213.75,236.25,258.75,281.25,303.75,326.25,348.75,371.25,393.75,416.25,438.75,461.25,483.75,506.25,528.75,551.25,573.75,596.25,618.75,641.25,663.75,686.25,708.75,731.25,753.75,776.25,798.75,821.25,843.75,866.25,888.75,911.25,933.75,956.25,978.75,1001.25,1023.75,1046.25,1068.75,1091.25,1113.75,1136.25,1158.75,1181.25,1203.75,1226.25,1248.75,1271.25,1293.75,1316.25,1338.75,1361.25,1383.75,1406.25,1428.75]
[M1] rank=1 service=productcatalogservice metric=istio-latency-90 baseline=0.004384 peak=0.087879 signed_z=999.0 onset_bin=33 onset_rel_s=753.75 persistence_bins=12
values_compact=delta:0.004409,-0.000017,-0.000004,0.000018,0.000008,-0.000015,-0.000008,-0.000007,0.000014,0.000005,-0.000017,-0.000002,-0.000004,-0.000007,0.000007,0.000001,0,-0.000005,0.000024,-0.000008,-0.000041,0.000002,0.000021,0.000002,-0.000003,0,-0.000002,0.000024,-0.000004,-0.000009,-0.000003,-0.000032,-0.000002,0.078331,0.004762,-0.002662,0.000536,0.001674,0.000415,-0.000704,-0.00181,-0.00483,-0.003037,-0.072103,-0.000464,-0.000106,-0.00001,0.000015,0,0.000001,0.000003,0.000016,0,0.000004,0.000038,0,-0.000019,0.000006,-0.000009,-0.00002,0.00001,-0.000003,0.000002,0.000003
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M2] rank=2 service=recommendationservice metric=istio-latency-90 baseline=0.009534 peak=0.093407 signed_z=999.0 onset_bin=33 onset_rel_s=753.75 persistence_bins=11
values_compact=raw:[0.009636,0.009641,0.009567,0.009563,0.009664,0.009635,0.009525,0.009543,0.009582,0.009531,0.009518,0.009561,0.009559,0.009482,0.009487,0.009487,0.009483,0.009461,0.009636,0.009639,0.009429,0.009423,0.009456,0.009494,0.009525,0.009543,0.009503,0.009527,0.009527,0.009518,0.009518,0.009462,0.00945,0.090327,0.093242,0.091786,0.091819,0.092924,0.093333,0.092788,0.092004,0.089532,0.088561,0.063394,0.009582,0.009445,0.009448,0.009498,0.009515,0.009492,0.009486,0.009481,0.00949,0.009542,0.009538,0.009504,0.009486,0.009501,0.009502,0.00956,0.009557,0.009466,0.009494,0.009463]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M3] rank=3 service=productcatalogservice metric=istio-latency-95 baseline=0.004702 peak=0.094266 signed_z=999.0 onset_bin=33 onset_rel_s=753.75 persistence_bins=12
values_compact=raw:[0.004719,0.004704,0.004701,0.004717,0.004724,0.004715,0.004706,0.0047,0.004714,0.00472,0.00471,0.004702,0.004695,0.004691,0.004696,0.004698,0.004699,0.004697,0.004718,0.004713,0.004679,0.00468,0.004697,0.004701,0.004697,0.004692,0.00469,0.004704,0.004701,0.004699,0.004698,0.00468,0.00468,0.091767,0.094055,0.092388,0.092668,0.093596,0.0938,0.093452,0.092627,0.090162,0.088549,0.061962,0.004782,0.004678,0.004674,0.004684,0.004684,0.004686,0.004687,0.004699,0.004698,0.004696,0.00472,0.004718,0.004704,0.004711,0.004708,0.004695,0.0047,0.004695,0.004696,0.004697]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M4] rank=4 service=recommendationservice metric=istio-latency-95 baseline=0.009821 peak=0.09698 signed_z=999.0 onset_bin=33 onset_rel_s=753.75 persistence_bins=11
values_compact=raw:[0.009913,0.009922,0.009848,0.009844,0.009952,0.009918,0.0098,0.009818,0.009855,0.009809,0.009795,0.009844,0.009838,0.009765,0.009775,0.00978,0.009775,0.009751,0.009934,0.009937,0.009729,0.009722,0.009749,0.009784,0.009811,0.009819,0.009784,0.009813,0.009813,0.009816,0.009816,0.009757,0.009743,0.095527,0.096894,0.095893,0.09591,0.096462,0.09667,0.096489,0.096108,0.094766,0.09428,0.081697,0.009891,0.009744,0.009746,0.009799,0.009815,0.009777,0.009772,0.009762,0.009771,0.009831,0.009827,0.009787,0.009773,0.009793,0.009793,0.00985,0.009845,0.009756,0.009783,0.009759]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M5] rank=5 service=productcatalogservice metric=istio-latency-99 baseline=0.004956 peak=0.099375 signed_z=999.0 onset_bin=33 onset_rel_s=753.75 persistence_bins=12
values_compact=delta:0.004967,-0.000014,-0.000001,0.000014,0.000006,-0.000005,-0.000009,-0.000006,0.000014,0.000007,-0.000004,-0.000013,-0.000008,-0.000002,0.000002,0.000004,0.000002,0,0.000017,-0.000002,-0.000028,0.000002,0.000013,0.000006,-0.000005,-0.000009,-0.000005,0.000009,-0.000003,0.000003,0.000001,-0.000008,0.000003,0.094092,0.000307,-0.000869,0.000075,0.000331,0.000036,-0.000064,-0.000036,-0.000573,-0.000474,-0.005381,-0.035091,-0.052358,0.000001,0.000006,0,0.000002,0,0.000008,0,-0.000007,0.000013,-0.000005,-0.000009,0.000007,0.000002,-0.000008,0,-0.000005,0,0
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M6] rank=6 service=gke-gke-cluster-default-pool-2e1807ce-0e4z metric=node-disk-reads-completed-total baseline=0.0 peak=0.044444 signed_z=999.0 onset_bin=33 onset_rel_s=753.75 persistence_bins=2
values_compact=rle:0*33,0.044444*2,0*29
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M7] rank=7 service=gke-gke-cluster-default-pool-2e1807ce-cx8g metric=node-disk-reads-completed-total baseline=0.0 peak=0.022222 signed_z=999.0 onset_bin=51 onset_rel_s=1158.75 persistence_bins=2
values_compact=rle:0*51,0.022222*2,0*11
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M8] rank=8 service=gke-gke-cluster-default-pool-2e1807ce-xte3 metric=node-disk-reads-completed-total baseline=0.0 peak=0.222222 signed_z=999.0 onset_bin=53 onset_rel_s=1203.75 persistence_bins=2
values_compact=rle:0*53,0.222222*2,0*9
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M9] rank=9 service=gke-gke-cluster-default-pool-2e1807ce-0e4z metric=node-disk-read-bytes-total baseline=0.0 peak=3822.933333 signed_z=999.0 onset_bin=33 onset_rel_s=753.75 persistence_bins=2
values_compact=rle:0*33,3822.933333*2,0*29
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M10] rank=10 service=gke-gke-cluster-default-pool-2e1807ce-cx8g metric=node-disk-read-bytes-total baseline=0.0 peak=91.022222 signed_z=999.0 onset_bin=51 onset_rel_s=1158.75 persistence_bins=2
values_compact=rle:0*51,91.022222*2,0*11
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M11] rank=11 service=gke-gke-cluster-default-pool-2e1807ce-xte3 metric=node-disk-read-bytes-total baseline=0.0 peak=10467.555556 signed_z=999.0 onset_bin=53 onset_rel_s=1203.75 persistence_bins=2
values_compact=rle:0*53,10467.555556*2,0*9
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M12] rank=12 service=recommendationservice metric=istio-latency-50 baseline=0.007244 peak=0.066696 signed_z=556.456 onset_bin=33 onset_rel_s=753.75 persistence_bins=11
values_compact=raw:[0.007418,0.007399,0.007323,0.00732,0.007359,0.007351,0.007321,0.007342,0.007401,0.007311,0.007271,0.007328,0.007324,0.007182,0.007171,0.007139,0.007146,0.00714,0.00725,0.007245,0.007031,0.007031,0.007112,0.007182,0.007239,0.00733,0.007265,0.007245,0.007246,0.007133,0.007133,0.007106,0.007106,0.029808,0.064026,0.058929,0.059096,0.064622,0.06609,0.063185,0.059177,0.038487,0.019688,0.007656,0.007116,0.007042,0.007064,0.007088,0.007113,0.007211,0.007201,0.007237,0.007238,0.007224,0.007274,0.007238,0.007196,0.007172,0.007175,0.007247,0.007222,0.007145,0.007188,0.007099]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[708.0,1010.0]

=== LOG SUMMARY ===
{"entries":[{"change_pct":-76.4,"n_during":381,"n_pre":1614,"service":"checkoutservice"},{"change_pct":-76.4,"n_during":127,"n_pre":538,"service":"emailservice"},{"change_pct":-76.4,"n_during":254,"n_pre":1076,"service":"paymentservice"},{"change_pct":-76.2,"n_during":2060,"n_pre":8644,"service":"shippingservice"},{"change_pct":-75.1,"n_during":3647,"n_pre":14637,"service":"cartservice"},{"change_pct":-75.1,"n_during":11264,"n_pre":45300,"service":"currencyservice"},{"change_pct":-75.1,"n_during":12676,"n_pre":50811,"service":"frontend"},{"change_pct":-75.0,"n_during":5,"n_pre":20,"service":"redis"}],"mode":"volume","omitted_services":2,"service_count":10}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":1685.7,"error_pct":0.0,"p95_during_ms":84.8935,"p95_pre_ms":4.754,"service":"recommendationservice","spans":27174},{"delta_pct":117.0,"error_pct":0.0,"p95_during_ms":124.025,"p95_pre_ms":57.16099999999997,"service":"frontend","spans":205449},{"delta_pct":47.5,"error_pct":0.0,"p95_during_ms":104.36699999999993,"p95_pre_ms":70.74669999999995,"service":"checkoutservice","spans":9018},{"delta_pct":22.1,"error_pct":0.0,"p95_during_ms":0.8334999999999999,"p95_pre_ms":0.6825000000000001,"service":"paymentservice","spans":953},{"delta_pct":-8.0,"error_pct":0.0,"p95_during_ms":0.023,"p95_pre_ms":0.025,"service":"productcatalogservice","spans":101846},{"delta_pct":1.1,"error_pct":0.0,"p95_during_ms":0.4512,"p95_pre_ms":0.44644999999999996,"service":"emailservice","spans":1241},{"delta_pct":0.4,"error_pct":0.0,"p95_during_ms":0.227,"p95_pre_ms":0.226,"service":"currencyservice","spans":56850}],"omitted_services":0,"service_count":7}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=3 omitted_edges=2
[{"evidence_source":"metric","onset_rel_s":732.0,"rank":1,"service":"productcatalogservice","severity_z":999.0},{"evidence_source":"trace","onset_rel_s":735.0,"rank":2,"service":"recommendationservice","severity_z":168.235},{"evidence_source":"trace","onset_rel_s":735.0,"rank":3,"service":"frontend","severity_z":39.049},{"evidence_source":"trace","onset_rel_s":735.0,"rank":4,"service":"checkoutservice","severity_z":11.658},{"evidence_source":"metric","onset_rel_s":750.0,"rank":5,"service":"gke-gke-cluster-default-pool-2e1807ce-0e4z","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":763.2,"rank":6,"service":"cartservice","severity_z":156.229},{"evidence_source":"metric","onset_rel_s":790.8,"rank":7,"service":"adservice","severity_z":550.508},{"evidence_source":"metric","onset_rel_s":1149.0,"rank":8,"service":"gke-gke-cluster-default-pool-2e1807ce-cx8g","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1192.8,"rank":9,"service":"gke-gke-cluster-default-pool-2e1807ce-xte3","severity_z":999.0},{"evidence_source":"none","onset_rel_s":null,"rank":10,"service":"redis","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":11,"service":"shippingservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":12,"service":"paymentservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":13,"service":"currencyservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":14,"service":"emailservice","severity_z":0.0}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"currencyservice","caller":"checkoutservice"},{"callee":"emailservice","caller":"checkoutservice"},{"callee":"paymentservice","caller":"checkoutservice"},{"callee":"productcatalogservice","caller":"checkoutservice"},{"callee":"checkoutservice","caller":"frontend"},{"callee":"currencyservice","caller":"frontend"},{"callee":"productcatalogservice","caller":"frontend"},{"callee":"recommendationservice","caller":"frontend"},{"callee":"productcatalogservice","caller":"recommendationservice"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

{"confidence":"high","reason":"Rank productcatalogservice first because productcatalogservice has direct istio-latency-90 evidence (signed-z 999, persistence 12 bins); although recommendationservice is salient, the caller path recommendationservice -> productcatalogservice means a disturbance in the callee can propagate back toward that caller-side symptom.","services":["productcatalogservice","recommendationservice"]}

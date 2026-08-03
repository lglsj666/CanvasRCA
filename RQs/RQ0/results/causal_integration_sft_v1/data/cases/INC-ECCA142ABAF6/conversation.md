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
opaque_id: INC-ECCA142ABAF6
observation_window={"duration_rel_s":1440.0,"source_metric_rows":1441}
selection_summary={"candidate_count":17,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":267,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["adservice","cartservice","checkoutservice","currencyservice","emailservice","frontend","frontend-external","gke-gke-cluster-default-pool-2e1807ce-0e4z","gke-gke-cluster-default-pool-2e1807ce-cx8g","gke-gke-cluster-default-pool-2e1807ce-w819","gke-gke-cluster-default-pool-2e1807ce-xte3","loadgenerator","paymentservice","productcatalogservice","recommendationservice","redis","shippingservice"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[11.25,33.75,56.25,78.75,101.25,123.75,146.25,168.75,191.25,213.75,236.25,258.75,281.25,303.75,326.25,348.75,371.25,393.75,416.25,438.75,461.25,483.75,506.25,528.75,551.25,573.75,596.25,618.75,641.25,663.75,686.25,708.75,731.25,753.75,776.25,798.75,821.25,843.75,866.25,888.75,911.25,933.75,956.25,978.75,1001.25,1023.75,1046.25,1068.75,1091.25,1113.75,1136.25,1158.75,1181.25,1203.75,1226.25,1248.75,1271.25,1293.75,1316.25,1338.75,1361.25,1383.75,1406.25,1428.75]
[M1] rank=1 service=productcatalogservice metric=container-memory-mapped-file baseline=0.0 peak=2207744.0 signed_z=999.0 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=rle:0*33,2207744*31
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M2] rank=2 service=productcatalogservice metric=istio-latency-90 baseline=0.004427 peak=0.083183 signed_z=999.0 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=raw:[0.004432,0.00442,0.004412,0.004428,0.004436,0.004459,0.004471,0.00445,0.004432,0.004428,0.004433,0.004419,0.004411,0.004406,0.004418,0.004483,0.004477,0.004423,0.004416,0.00442,0.004438,0.004428,0.004422,0.004418,0.004412,0.004417,0.004406,0.004404,0.004419,0.004427,0.004411,0.004401,0.004422,0.06867,0.079646,0.081247,0.081586,0.081648,0.081614,0.08207,0.081671,0.081125,0.082308,0.082053,0.080679,0.08042,0.080624,0.080382,0.080894,0.080989,0.080968,0.082455,0.083136,0.082147,0.080915,0.081022,0.081302,0.081747,0.081861,0.080735,0.080313,0.080619,0.080543,0.081088]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M3] rank=3 service=recommendationservice metric=istio-latency-90 baseline=0.009607 peak=0.093159 signed_z=999.0 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=raw:[0.009712,0.009573,0.009562,0.009654,0.009708,0.009807,0.009842,0.009616,0.009529,0.009629,0.00963,0.009562,0.009571,0.009564,0.009609,0.009693,0.009652,0.009565,0.00952,0.009531,0.009561,0.009534,0.009544,0.009584,0.009614,0.009601,0.009539,0.009548,0.009561,0.009601,0.009619,0.009615,0.009594,0.085562,0.091485,0.091474,0.091233,0.091538,0.091304,0.091195,0.091317,0.091149,0.092083,0.091602,0.090488,0.090887,0.091126,0.090155,0.08952,0.090721,0.092463,0.093087,0.09239,0.091718,0.091556,0.091353,0.09107,0.090994,0.091601,0.091743,0.091335,0.091778,0.091412,0.091143]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M4] rank=4 service=productcatalogservice metric=istio-latency-95 baseline=0.004724 peak=0.091592 signed_z=999.0 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=raw:[0.004727,0.004716,0.004712,0.004725,0.004731,0.004749,0.004761,0.004739,0.004723,0.004722,0.004726,0.004718,0.004713,0.004711,0.004721,0.00478,0.004773,0.004718,0.004712,0.004714,0.004726,0.004722,0.004718,0.004717,0.004712,0.004714,0.004707,0.004705,0.004714,0.004723,0.004714,0.004704,0.004719,0.084335,0.089823,0.090623,0.090793,0.090824,0.090807,0.091035,0.090836,0.090562,0.091154,0.091026,0.090355,0.090243,0.090344,0.090191,0.090447,0.090494,0.090484,0.091227,0.091568,0.091074,0.090457,0.090511,0.090651,0.090873,0.090931,0.090368,0.090156,0.09031,0.090272,0.090544]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M5] rank=5 service=gke-gke-cluster-default-pool-2e1807ce-0e4z metric=node-disk-reads-completed-total baseline=0.0 peak=0.022222 signed_z=999.0 onset_bin=54 onset_rel_s=1226.25 persistence_bins=2
values_compact=rle:0*54,0.022222*2,0*8
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M6] rank=6 service=gke-gke-cluster-default-pool-2e1807ce-cx8g metric=node-disk-reads-completed-total baseline=0.0 peak=0.111111 signed_z=999.0 onset_bin=39 onset_rel_s=888.75 persistence_bins=9
values_compact=rle:0*39,0.044444*2,0.022222*2,0*10,0.044444*2,0*2,0.111111*2,0*4,0.022222*1
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M7] rank=7 service=gke-gke-cluster-default-pool-2e1807ce-xte3 metric=node-disk-reads-completed-total baseline=0.0 peak=3.311111 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=rle:0*63,3.311111*1
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M8] rank=8 service=gke-gke-cluster-default-pool-2e1807ce-0e4z metric=node-disk-read-bytes-total baseline=0.0 peak=1820.444444 signed_z=999.0 onset_bin=54 onset_rel_s=1226.25 persistence_bins=2
values_compact=rle:0*54,1820.444444*2,0*8
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M9] rank=9 service=gke-gke-cluster-default-pool-2e1807ce-cx8g metric=node-disk-read-bytes-total baseline=0.0 peak=8374.044444 signed_z=999.0 onset_bin=39 onset_rel_s=888.75 persistence_bins=9
values_compact=rle:0*39,182.044444*2,91.022222*2,0*10,3185.777778*2,0*2,8374.044444*2,0*4,1547.377778*1
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M10] rank=10 service=gke-gke-cluster-default-pool-2e1807ce-xte3 metric=node-disk-read-bytes-total baseline=0.0 peak=115143.111111 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=rle:0*63,115143.111111*1
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M11] rank=11 service=recommendationservice metric=istio-latency-50 baseline=0.007484 peak=0.062056 signed_z=950.704 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=raw:[0.007587,0.007494,0.007494,0.007551,0.00757,0.007612,0.007624,0.007483,0.007443,0.007511,0.0075,0.007478,0.0075,0.007466,0.007462,0.007534,0.007512,0.007457,0.007434,0.007443,0.007452,0.007416,0.007417,0.007452,0.007457,0.007433,0.007409,0.007413,0.007428,0.007489,0.007513,0.007479,0.007451,0.009185,0.057427,0.056056,0.054302,0.05726,0.056522,0.055975,0.056587,0.055744,0.060417,0.058009,0.05244,0.054435,0.055629,0.050775,0.040426,0.053606,0.058962,0.061675,0.061213,0.058592,0.057781,0.056764,0.055349,0.05497,0.058006,0.058713,0.056674,0.058889,0.057059,0.055714]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M12] rank=12 service=emailservice metric=istio-latency-99 baseline=0.005536 peak=0.405 signed_z=330.503 onset_bin=49 onset_rel_s=1113.75 persistence_bins=5
values_compact=rle:0.00496*2,0.0079*1,0.0082*1,0.00496*4,0.0082*1,0.0086*1,0.00496*5,0.0078*1,0.00765*1,0.00496*16,0.0084*2,0.00496*1,0.0086*2,0.00815*1,0.008*1,0.00496*3,0.00875*1,0.009367*1,0.0078*1,0.00496*3,0.00935*1,0.39*1,0.38*1,0.00496*9,0.022375*1,0.022*1,0.00496*1
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[713.0,1440.0]

=== LOG SUMMARY ===
{"entries":[{"change_pct":-33.3,"n_during":10,"n_pre":15,"service":"redis"},{"change_pct":12.6,"n_during":966,"n_pre":858,"service":"checkoutservice"},{"change_pct":12.6,"n_during":322,"n_pre":286,"service":"emailservice"},{"change_pct":12.6,"n_during":644,"n_pre":572,"service":"paymentservice"},{"change_pct":4.0,"n_during":5274,"n_pre":5070,"service":"shippingservice"},{"change_pct":-2.9,"n_during":5237,"n_pre":5394,"service":"adservice"},{"change_pct":-1.6,"n_during":6527,"n_pre":6633,"service":"recommendationservice"},{"change_pct":-1.3,"n_during":28092,"n_pre":28454,"service":"currencyservice"}],"mode":"volume","omitted_services":2,"service_count":10}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":1559.6,"error_pct":0.0,"p95_during_ms":83.90355,"p95_pre_ms":5.055799999999996,"service":"recommendationservice","spans":26896},{"delta_pct":186.1,"error_pct":0.0,"p95_during_ms":172.4097999999991,"p95_pre_ms":60.25899999999982,"service":"frontend","spans":204540},{"delta_pct":48.8,"error_pct":0.0,"p95_during_ms":115.01765000000005,"p95_pre_ms":77.30625,"service":"checkoutservice","spans":8576},{"delta_pct":14.3,"error_pct":0.0,"p95_during_ms":0.032,"p95_pre_ms":0.028,"service":"productcatalogservice","spans":101361},{"delta_pct":-4.1,"error_pct":0.0,"p95_during_ms":0.4,"p95_pre_ms":0.4168999999999998,"service":"emailservice","spans":1184},{"delta_pct":0.9,"error_pct":0.0,"p95_during_ms":0.228,"p95_pre_ms":0.226,"service":"currencyservice","spans":56834},{"delta_pct":-0.6,"error_pct":0.0,"p95_during_ms":0.444,"p95_pre_ms":0.44674999999999976,"service":"paymentservice","spans":896}],"omitted_services":0,"service_count":7}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=3 omitted_edges=1
[{"evidence_source":"trace","onset_rel_s":735.0,"rank":1,"service":"recommendationservice","severity_z":158.997},{"evidence_source":"trace","onset_rel_s":735.0,"rank":2,"service":"frontend","severity_z":21.226},{"evidence_source":"metric","onset_rel_s":736.8,"rank":3,"service":"productcatalogservice","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":771.0,"rank":4,"service":"currencyservice","severity_z":13.18},{"evidence_source":"trace","onset_rel_s":795.0,"rank":5,"service":"checkoutservice","severity_z":12.356},{"evidence_source":"metric","onset_rel_s":961.8,"rank":6,"service":"adservice","severity_z":88.775},{"evidence_source":"metric","onset_rel_s":1135.8,"rank":7,"service":"emailservice","severity_z":330.503},{"evidence_source":"metric","onset_rel_s":1207.8,"rank":8,"service":"gke-gke-cluster-default-pool-2e1807ce-0e4z","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1273.2,"rank":9,"service":"gke-gke-cluster-default-pool-2e1807ce-cx8g","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1425.0,"rank":10,"service":"gke-gke-cluster-default-pool-2e1807ce-xte3","severity_z":999.0},{"evidence_source":"none","onset_rel_s":null,"rank":11,"service":"cartservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":12,"service":"shippingservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":13,"service":"redis","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":14,"service":"paymentservice","severity_z":0.0}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"currencyservice","caller":"checkoutservice"},{"callee":"emailservice","caller":"checkoutservice"},{"callee":"paymentservice","caller":"checkoutservice"},{"callee":"productcatalogservice","caller":"checkoutservice"},{"callee":"checkoutservice","caller":"frontend"},{"callee":"currencyservice","caller":"frontend"},{"callee":"productcatalogservice","caller":"frontend"},{"callee":"recommendationservice","caller":"frontend"},{"callee":"productcatalogservice","caller":"recommendationservice"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

{"confidence":"high","reason":"Rank productcatalogservice first because productcatalogservice has direct container-memory-mapped-file evidence (signed-z 999, persistence 31 bins); although recommendationservice is salient, the caller path recommendationservice -> productcatalogservice means a disturbance in the callee can propagate back toward that caller-side symptom.","services":["productcatalogservice","recommendationservice"]}

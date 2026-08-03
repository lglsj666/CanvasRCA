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
opaque_id: INC-5500A2398DF7
observation_window={"duration_rel_s":1440.0,"source_metric_rows":1441}
selection_summary={"candidate_count":17,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":262,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["adservice","cartservice","checkoutservice","currencyservice","emailservice","frontend","frontend-external","gke-gke-cluster-default-pool-2e1807ce-0e4z","gke-gke-cluster-default-pool-2e1807ce-cx8g","gke-gke-cluster-default-pool-2e1807ce-w819","gke-gke-cluster-default-pool-2e1807ce-xte3","loadgenerator","paymentservice","productcatalogservice","recommendationservice","redis","shippingservice"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[11.25,33.75,56.25,78.75,101.25,123.75,146.25,168.75,191.25,213.75,236.25,258.75,281.25,303.75,326.25,348.75,371.25,393.75,416.25,438.75,461.25,483.75,506.25,528.75,551.25,573.75,596.25,618.75,641.25,663.75,686.25,708.75,731.25,753.75,776.25,798.75,821.25,843.75,866.25,888.75,911.25,933.75,956.25,978.75,1001.25,1023.75,1046.25,1068.75,1091.25,1113.75,1136.25,1158.75,1181.25,1203.75,1226.25,1248.75,1271.25,1293.75,1316.25,1338.75,1361.25,1383.75,1406.25,1428.75]
[M1] rank=1 service=currencyservice metric=container-memory-mapped-file baseline=0.0 peak=2207744.0 signed_z=999.0 onset_bin=32 onset_rel_s=731.25 persistence_bins=32
values_compact=rle:0*32,2207744*32
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M2] rank=2 service=gke-gke-cluster-default-pool-2e1807ce-0e4z metric=node-disk-reads-completed-total baseline=0.0 peak=0.066667 signed_z=999.0 onset_bin=34 onset_rel_s=776.25 persistence_bins=2
values_compact=rle:0*34,0.066667*2,0*28
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M3] rank=3 service=gke-gke-cluster-default-pool-2e1807ce-0e4z metric=node-disk-read-bytes-total baseline=0.0 peak=273.066667 signed_z=999.0 onset_bin=34 onset_rel_s=776.25 persistence_bins=2
values_compact=rle:0*34,273.066667*2,0*28
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M4] rank=4 service=currencyservice metric=istio-latency-50 baseline=0.004071 peak=0.054962 signed_z=401.099 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=raw:[0.00429,0.00406,0.00404,0.004134,0.004107,0.004087,0.004059,0.003979,0.003931,0.004068,0.004108,0.00419,0.004219,0.004059,0.004216,0.004202,0.004031,0.004118,0.00414,0.004023,0.003845,0.0039,0.003952,0.003888,0.003955,0.003901,0.003913,0.003982,0.004067,0.004214,0.004353,0.00418,0.004242,0.007019,0.040951,0.036752,0.037946,0.035498,0.038265,0.042714,0.033981,0.043724,0.050278,0.047966,0.037895,0.040876,0.050468,0.050862,0.052905,0.054528,0.050016,0.039643,0.038598,0.033773,0.035202,0.042249,0.041527,0.039791,0.044691,0.052473,0.050336,0.041601,0.04037,0.047137]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M5] rank=5 service=cartservice metric=istio-latency-95 baseline=0.005479 peak=0.405515 signed_z=362.34 onset_bin=38 onset_rel_s=866.25 persistence_bins=13
values_compact=raw:[0.006569,0.004918,0.00496,0.006092,0.008661,0.008327,0.004983,0.004919,0.004923,0.004976,0.004984,0.004912,0.004907,0.004995,0.005082,0.004988,0.004924,0.004989,0.008165,0.004988,0.004888,0.004938,0.004951,0.004911,0.004897,0.004947,0.004974,0.004914,0.004889,0.005696,0.006368,0.004952,0.004938,0.006321,0.007235,0.007084,0.007686,0.007701,0.009059,0.0115,0.008062,0.007363,0.0875,0.3375,0.009003,0.008088,0.00752,0.00759,0.008451,0.14625,0.189531,0.008758,0.007854,0.00853,0.008574,0.007628,0.008241,0.009343,0.00916,0.009702,0.106,0.15125,0.01675,0.008317]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M6] rank=6 service=currencyservice metric=container-sockets baseline=4.0 peak=6.0 signed_z=333.333 onset_bin=32 onset_rel_s=731.25 persistence_bins=32
values_compact=rle:4*32,6*32
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M7] rank=7 service=currencyservice metric=container-memory-cache baseline=40960.0 peak=2248704.0 signed_z=314.35 onset_bin=32 onset_rel_s=731.25 persistence_bins=32
values_compact=rle:40960*32,2248704*32
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M8] rank=8 service=currencyservice metric=istio-latency-99 baseline=0.095645 peak=0.221769 signed_z=155.788 onset_bin=33 onset_rel_s=753.75 persistence_bins=31
values_compact=raw:[0.096139,0.095398,0.094494,0.095374,0.095526,0.096631,0.096131,0.095184,0.095173,0.094532,0.094621,0.095692,0.095901,0.096063,0.096387,0.096151,0.095772,0.095535,0.096075,0.095701,0.094198,0.095397,0.095406,0.094822,0.095623,0.094994,0.094791,0.096515,0.096297,0.096921,0.097717,0.096552,0.096607,0.099196,0.099689,0.099236,0.09976,0.09968,0.15475,0.169978,0.099483,0.099716,0.127848,0.09962,0.099386,0.155415,0.166286,0.099916,0.181312,0.220917,0.208905,0.099665,0.099781,0.099624,0.09967,0.099486,0.099122,0.099444,0.169844,0.219174,0.213268,0.13444,0.12868,0.099877]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M9] rank=9 service=recommendationservice metric=istio-latency-95 baseline=0.009829 peak=0.015341 signed_z=117.858 onset_bin=43 onset_rel_s=978.75 persistence_bins=9
values_compact=raw:[0.009881,0.009849,0.009815,0.009788,0.009915,0.009916,0.009801,0.009814,0.009797,0.009789,0.009778,0.009791,0.009799,0.009798,0.009802,0.009801,0.009791,0.009904,0.009907,0.0098,0.009805,0.009813,0.009838,0.009785,0.009778,0.00991,0.009906,0.009797,0.009797,0.009855,0.009886,0.009819,0.00977,0.00992,0.009959,0.009839,0.009954,0.009925,0.009947,0.013244,0.009903,0.009813,0.009876,0.01217,0.009997,0.009869,0.00988,0.009858,0.009825,0.013842,0.015341,0.009882,0.009867,0.009965,0.009976,0.009916,0.009935,0.010471,0.009933,0.009981,0.010667,0.009976,0.009947,0.009906]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M10] rank=10 service=checkoutservice metric=istio-latency-90 baseline=0.222785 peak=1.625 signed_z=68.451 onset_bin=33 onset_rel_s=753.75 persistence_bins=29
values_compact=raw:[0.221429,0.222857,0.232115,0.246087,0.247,0.232656,0.222069,0.191364,0.2,0.219375,0.225156,0.2275,0.225556,0.22,0.22,0.2182,0.212059,0.22,0.225769,0.219318,0.198571,0.202187,0.2075,0.221364,0.2248,0.221875,0.215909,0.202692,0.236875,0.235,0.227031,0.231143,0.241875,0.359375,0.384091,0.308333,0.364286,0.4175,0.439286,0.428571,0.4075,0.430769,0.925,1.15,0.492857,0.441667,0.408333,0.428571,0.490625,0.5,0.491667,0.447222,0.425,0.420833,0.7,0.625,0.28,0.35,0.455,0.440625,0.4,0.246818,0.45,1.5]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M11] rank=11 service=cartservice metric=istio-latency-90 baseline=0.004767 peak=0.009206 signed_z=66.787 onset_bin=38 onset_rel_s=866.25 persistence_bins=25
values_compact=raw:[0.004871,0.004712,0.004752,0.004826,0.004917,0.004911,0.004774,0.004713,0.004717,0.004767,0.004775,0.004706,0.004701,0.004785,0.004793,0.004778,0.004718,0.004779,0.004891,0.004778,0.004684,0.004731,0.004743,0.004705,0.004692,0.004739,0.004765,0.004708,0.004684,0.004811,0.004843,0.004744,0.004731,0.004861,0.004952,0.004935,0.004941,0.004936,0.006152,0.007323,0.005332,0.004966,0.007007,0.008285,0.00572,0.005196,0.004992,0.005097,0.006258,0.00778,0.007541,0.006293,0.005626,0.006105,0.006235,0.00517,0.005602,0.006771,0.006788,0.006904,0.007281,0.00719,0.005934,0.005356]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23
[M12] rank=12 service=emailservice metric=istio-latency-95 baseline=0.004817 peak=0.006875 signed_z=58.713 onset_bin=44 onset_rel_s=1001.25 persistence_bins=4
values_compact=rle:0.004897*1,0.004909*1,0.0048*2,0.00489*1,0.004888*1,0.0048*12,0.004897*1,0.004884*1,0.0048*24,0.006333*1,0.0065*1,0.0048*2,0.004883*2,0.0048*4,0.004906*1,0.00489*1,0.0048*1,0.005125*1,0.006875*1,0.0048*5
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,22,23,23

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[707.0,1440.0]

=== LOG SUMMARY ===
{"entries":[{"change_pct":50.0,"n_during":15,"n_pre":10,"service":"redis"},{"change_pct":-5.4,"n_during":990,"n_pre":1047,"service":"checkoutservice"},{"change_pct":-5.4,"n_during":330,"n_pre":349,"service":"emailservice"},{"change_pct":-5.4,"n_during":660,"n_pre":698,"service":"paymentservice"},{"change_pct":-1.7,"n_during":5356,"n_pre":5448,"service":"shippingservice"},{"change_pct":-1.3,"n_during":31334,"n_pre":31753,"service":"frontend"},{"change_pct":-1.2,"n_during":27908,"n_pre":28241,"service":"currencyservice"},{"change_pct":-1.1,"n_during":9112,"n_pre":9211,"service":"cartservice"}],"mode":"volume","omitted_services":2,"service_count":10}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":114.5,"error_pct":0.0,"p95_during_ms":164.2158000000029,"p95_pre_ms":76.55579999999999,"service":"checkoutservice","spans":9364},{"delta_pct":106.9,"error_pct":0.0,"p95_during_ms":143.84859999999986,"p95_pre_ms":69.52149999999989,"service":"frontend","spans":205669},{"delta_pct":15.1,"error_pct":0.0,"p95_during_ms":0.29,"p95_pre_ms":0.25194999999999707,"service":"currencyservice","spans":56434},{"delta_pct":10.7,"error_pct":0.0,"p95_during_ms":5.038,"p95_pre_ms":4.55065,"service":"recommendationservice","spans":27340},{"delta_pct":10.0,"error_pct":0.0,"p95_during_ms":0.37825,"p95_pre_ms":0.344,"service":"paymentservice","spans":967},{"delta_pct":-3.1,"error_pct":0.0,"p95_during_ms":0.4138499999999998,"p95_pre_ms":0.427,"service":"emailservice","spans":1255},{"delta_pct":0.0,"error_pct":0.0,"p95_during_ms":0.024,"p95_pre_ms":0.024,"service":"productcatalogservice","spans":102771}],"omitted_services":0,"service_count":7}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=3 omitted_edges=0
[{"evidence_source":"trace","onset_rel_s":735.0,"rank":1,"service":"frontend","severity_z":17.528},{"evidence_source":"metric","onset_rel_s":757.2,"rank":2,"service":"gke-gke-cluster-default-pool-2e1807ce-0e4z","severity_z":999.0},{"evidence_source":"trace","onset_rel_s":855.0,"rank":3,"service":"checkoutservice","severity_z":11.612},{"evidence_source":"metric","onset_rel_s":888.0,"rank":4,"service":"recommendationservice","severity_z":117.858},{"evidence_source":"metric","onset_rel_s":970.2,"rank":5,"service":"cartservice","severity_z":362.34},{"evidence_source":"metric","onset_rel_s":985.2,"rank":6,"service":"emailservice","severity_z":58.713},{"evidence_source":"trace","onset_rel_s":1005.0,"rank":7,"service":"currencyservice","severity_z":3.81},{"evidence_source":"metric","onset_rel_s":1177.8,"rank":8,"service":"gke-gke-cluster-default-pool-2e1807ce-xte3","severity_z":11.37},{"evidence_source":"none","onset_rel_s":null,"rank":9,"service":"adservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":10,"service":"productcatalogservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":11,"service":"redis","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":12,"service":"gke-gke-cluster-default-pool-2e1807ce-w819","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":13,"service":"frontend-external","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":14,"service":"loadgenerator","severity_z":0.0}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"currencyservice","caller":"checkoutservice"},{"callee":"emailservice","caller":"checkoutservice"},{"callee":"productcatalogservice","caller":"checkoutservice"},{"callee":"checkoutservice","caller":"frontend"},{"callee":"currencyservice","caller":"frontend"},{"callee":"productcatalogservice","caller":"frontend"},{"callee":"recommendationservice","caller":"frontend"},{"callee":"productcatalogservice","caller":"recommendationservice"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

{"confidence":"high","reason":"Rank currencyservice first because currencyservice has direct container-memory-mapped-file evidence (signed-z 999, persistence 32 bins); although frontend is salient, the caller path frontend -> currencyservice means a disturbance in the callee can propagate back toward that caller-side symptom.","services":["currencyservice","frontend"]}

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
opaque_id: INC-5CB058246CEE
observation_window={"duration_rel_s":929.0,"source_metric_rows":930}
selection_summary={"candidate_count":18,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":264,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["InboundPassthroughClusterIpv4","PassthroughCluster","adservice","cartservice","checkoutservice","currencyservice","emailservice","frontend","frontend-external","gke-gke-cluster-default-pool-c49c2b06-crhc","gke-gke-cluster-default-pool-c49c2b06-d258","gke-gke-cluster-default-pool-c49c2b06-vlhn","loadgenerator","paymentservice","productcatalogservice","recommendationservice","redis","shippingservice"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[7.258,21.773,36.289,50.805,65.32,79.836,94.352,108.867,123.383,137.898,152.414,166.93,181.445,195.961,210.477,224.992,239.508,254.023,268.539,283.055,297.57,312.086,326.602,341.117,355.633,370.148,384.664,399.18,413.695,428.211,442.727,457.242,471.758,486.273,500.789,515.305,529.82,544.336,558.852,573.367,587.883,602.398,616.914,631.43,645.945,660.461,674.977,689.492,704.008,718.523,733.039,747.555,762.07,776.586,791.102,805.617,820.133,834.648,849.164,863.68,878.195,892.711,907.227,921.742]
[M1] rank=1 service=checkoutservice metric=container-memory-mapped-file baseline=0.0 peak=2207744.0 signed_z=999.0 onset_bin=51 onset_rel_s=747.555 persistence_bins=13
values_compact=rle:0*51,2207744*13
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:15,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,15
[M2] rank=2 service=frontend-external metric=istio-error-total baseline=0.0 peak=7.267 signed_z=999.0 onset_bin=62 onset_rel_s=907.227 persistence_bins=2
values_compact=rle:0*62,7.267*2
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:15,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,15
[M3] rank=3 service=cartservice metric=istio-bytes-90 baseline=0.247268 peak=1.067931 signed_z=999.0 onset_bin=61 onset_rel_s=892.711 persistence_bins=2
values_compact=raw:[0.24723,0.247231,0.247208,0.247338,0.247454,0.247056,0.247058,0.247115,0.247156,0.247376,0.247003,0.24757,0.247179,0.247377,0.247168,0.247409,0.247088,0.247273,0.247225,0.247467,0.247364,0.24713,0.247107,0.247285,0.247254,0.247285,0.24744,0.247262,0.247373,0.247411,0.247301,0.247338,0.246857,0.247069,0.247181,0.247502,0.247576,0.247273,0.247148,0.247162,0.247484,0.247345,0.247092,0.247177,0.247414,0.247478,0.247248,0.247273,0.247176,0.247249,0.247344,0.247332,0.247388,0.247451,0.247226,0.246956,0.247049,0.247238,0.247427,0.247489,0.247565,0.246646,0.246375,0.24708]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:15,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,15
[M4] rank=4 service=currencyservice metric=istio-bytes-90 baseline=0.24446 peak=1.484949 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=raw:[0.24487,0.244483,0.244943,0.244542,0.244857,0.243873,0.243708,0.244441,0.243856,0.244844,0.243947,0.245168,0.244354,0.24466,0.244103,0.244655,0.244283,0.24492,0.24437,0.244654,0.244279,0.244323,0.244525,0.244604,0.244659,0.244193,0.244679,0.244385,0.244688,0.244824,0.24494,0.2444,0.244472,0.243466,0.244554,0.244721,0.245512,0.243968,0.244351,0.244003,0.245109,0.244528,0.244312,0.244262,0.244349,0.244709,0.24413,0.244664,0.244736,0.244403,0.2442,0.244181,0.244858,0.244838,0.244544,0.243992,0.243807,0.244685,0.245022,0.245241,0.245666,0.245127,0.246007,0.24564]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:15,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,15
[M5] rank=5 service=productcatalogservice metric=istio-bytes-99 baseline=2.32462 peak=0.227139 signed_z=-999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=raw:[2.324278,2.324359,2.324625,2.325107,2.324565,2.324572,2.323709,2.324718,2.324894,2.325265,2.325035,2.32491,2.32454,2.324947,2.324225,2.325098,2.323606,2.324927,2.324086,2.324938,2.324507,2.324753,2.324392,2.324622,2.324206,2.325089,2.325089,2.324209,2.325131,2.323947,2.324739,2.324594,2.324775,2.32476,2.324694,2.324963,2.325208,2.324459,2.324724,2.32371,2.325106,2.323827,2.325213,2.32471,2.325144,2.324399,2.324737,2.325147,2.324935,2.324261,2.324607,2.324797,2.32442,2.324451,2.324267,2.324229,2.324252,2.324364,2.325367,2.324951,2.324007,2.325272,2.325896,2.323374]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:15,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,15
[M6] rank=6 service=adservice metric=istio-bytes-99 baseline=2.319947 peak=0.2194 signed_z=-991.989 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=raw:[2.32,2.32,2.320508,2.317857,2.319167,2.320566,2.3225,2.322105,2.319732,2.318636,2.315755,2.320833,2.321389,2.322455,2.319737,2.320263,2.320263,2.32,2.320545,2.319182,2.319474,2.319741,2.319741,2.321053,2.317981,2.319444,2.319444,2.321579,2.319196,2.32,2.321339,2.32,2.318684,2.31819,2.319737,2.321297,2.322368,2.318966,2.317962,2.319274,2.32,2.322845,2.319455,2.321909,2.320268,2.321636,2.319727,2.320577,2.318302,2.319444,2.318661,2.321316,2.322105,2.321579,2.318684,2.318684,2.32,2.321364,2.319182,2.318364,2.321415,2.322885,2.326176,2.315749]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:15,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,13
[M7] rank=7 service=recommendationservice metric=istio-bytes-99 baseline=2.31996 peak=0.2485 signed_z=-980.08 onset_bin=61 onset_rel_s=892.711 persistence_bins=3
values_compact=raw:[2.323355,2.320192,2.319241,2.316,2.321875,2.32125,2.32125,2.318986,2.319167,2.320417,2.319577,2.319366,2.320208,2.318125,2.318732,2.315652,2.3215,2.320857,2.325137,2.321233,2.3216,2.320203,2.317973,2.318732,2.317537,2.321567,2.318099,2.321558,2.319231,2.322308,2.319013,2.319803,2.318816,2.3206,2.322,2.318954,2.319792,2.316957,2.319782,2.321216,2.319167,2.324014,2.316194,2.32169,2.317429,2.321324,2.317537,2.320231,2.320652,2.322391,2.321071,2.321458,2.319786,2.319786,2.317708,2.319366,2.321233,2.320423,2.317353,2.319091,2.323364,2.313036,2.304571,2.266019]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:15,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,13
[M8] rank=8 service=gke-gke-cluster-default-pool-c49c2b06-crhc metric=node-memory-active-bytes baseline=11119.000621 peak=19111844.977778 signed_z=894.361 onset_bin=1 onset_rel_s=21.773 persistence_bins=5
values_compact=delta:5461.333333,71998.577778,-1547.377778,-273.066666,-71452.444445,455.111111,-182.044444,-728.177778,182.044445,637.155555,819.2,-1274.311111,-546.133333,-637.155556,546.133333,182.044445,637.155555,91.022223,364.088889,-637.155556,819.2,-364.088889,-91.022222,-637.155556,-91.022222,-91.022222,182.044444,91.022223,637.155555,91.022222,-1274.311111,-273.066666,273.066666,2275.555556,91.022222,1001.244444,-1001.244444,-728.177778,-1547.377778,0,91.022223,728.177777,-546.133333,-91.022222,-546.133333,1638.4,910.222222,-273.066667,-728.177778,2184.533334,910.222222,-728.177778,-910.222222,-910.222222,455.111111,-955.733334,-955.733333,273.066667,-273.066667,455.111111,0,-455.111111,612670.577778,1059680.711111
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:15,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,15
[M9] rank=9 service=cartservice metric=istio-latency-95 baseline=0.00807 peak=0.403309 signed_z=757.111 onset_bin=43 onset_rel_s=631.43 persistence_bins=4
values_compact=raw:[0.008608,0.008725,0.008411,0.007991,0.007526,0.008317,0.008207,0.008083,0.006637,0.007385,0.008424,0.00856,0.008544,0.007921,0.007947,0.008291,0.008192,0.008372,0.009056,0.008813,0.008712,0.007998,0.007514,0.007612,0.007318,0.00725,0.007623,0.008029,0.008129,0.008152,0.008044,0.008038,0.008009,0.008031,0.007954,0.007737,0.007125,0.007283,0.007536,0.007695,0.007369,0.007826,0.008174,0.009942,0.332422,0.400368,0.311458,0.009624,0.00896,0.00719,0.007362,0.007092,0.007017,0.007387,0.007624,0.007522,0.00697,0.006865,0.006991,0.007357,0.006689,0.007206,0.007381,0.008747]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:15,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,15
[M10] rank=10 service=productcatalogservice metric=istio-bytes-90 baseline=0.245717 peak=0.09816 signed_z=-667.471 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=raw:[0.245671,0.24568,0.245708,0.245769,0.2457,0.245703,0.245592,0.245739,0.245761,0.245815,0.245773,0.245761,0.245707,0.245767,0.245656,0.245778,0.245566,0.24576,0.245651,0.245766,0.245708,0.245718,0.245679,0.245718,0.245674,0.245783,0.245783,0.245663,0.245789,0.245627,0.245737,0.245715,0.245733,0.245734,0.245733,0.245785,0.245814,0.245701,0.245733,0.245592,0.245793,0.245615,0.245802,0.245743,0.245804,0.245699,0.245733,0.245799,0.245771,0.245682,0.245718,0.24575,0.245685,0.245681,0.245647,0.245649,0.245654,0.245674,0.245835,0.24578,0.24565,0.245805,0.245873,0.245333]
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:15,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,15
[M11] rank=11 service=currencyservice metric=container-sockets baseline=4.0 peak=2.0 signed_z=-500.0 onset_bin=61 onset_rel_s=892.711 persistence_bins=3
values_compact=rle:4*61,2*3
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:15,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,15
[M12] rank=12 service=emailservice metric=istio-latency-95 baseline=0.004841 peak=0.057789 signed_z=480.11 onset_bin=60 onset_rel_s=878.195 persistence_bins=3
values_compact=rle:0.0048*17,0.004878*1,0.004954*1,0.005417*1,0.004943*1,0.004863*1,0.0048*5,0.004849*1,0.004854*1,0.004862*1,0.0048*1,0.004867*1,0.004925*1,0.004936*1,0.004868*1,0.0048*6,0.004884*2,0.004876*1,0.004873*1,0.0048*10,0.004886*1,0.004873*1,0.004868*1,0.0048*1,0.004903*1,0.05125*1,0.01*1,0.057609*1,0.0048*1
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:15,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,14,15,15

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[729.0,929.0]

=== LOG SUMMARY ===
{"entries":[{"error_logs":178,"error_pct":0.45,"service":"frontend","total_logs":39742}],"mode":"errors","omitted_services":9,"service_count":10}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":87.4,"error_pct":0.0,"p95_during_ms":137.5505,"p95_pre_ms":73.38119999999999,"service":"checkoutservice","spans":4963},{"delta_pct":62.4,"error_pct":0.0,"p95_during_ms":0.6351499999999994,"p95_pre_ms":0.391,"service":"emailservice","spans":652},{"delta_pct":-55.1,"error_pct":0.0,"p95_during_ms":0.36419999999999997,"p95_pre_ms":0.8115999999999984,"service":"paymentservice","spans":513},{"delta_pct":22.2,"error_pct":0.0,"p95_during_ms":5.6644999999999985,"p95_pre_ms":4.6357499999999945,"service":"recommendationservice","spans":13656},{"delta_pct":9.0,"error_pct":0.0,"p95_during_ms":0.219,"p95_pre_ms":0.201,"service":"currencyservice","spans":27575},{"delta_pct":3.6,"error_pct":0.0,"p95_during_ms":59.54559999999992,"p95_pre_ms":57.493399999999994,"service":"frontend","spans":101662},{"delta_pct":0.0,"error_pct":0.0,"p95_during_ms":0.025,"p95_pre_ms":0.025,"service":"productcatalogservice","spans":50939}],"omitted_services":0,"service_count":7}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=2 omitted_edges=0
[{"evidence_source":"metric","onset_rel_s":643.2,"rank":1,"service":"frontend","severity_z":34.327},{"evidence_source":"trace","onset_rel_s":745.2,"rank":2,"service":"checkoutservice","severity_z":4.921},{"evidence_source":"metric","onset_rel_s":871.8,"rank":3,"service":"emailservice","severity_z":480.11},{"evidence_source":"metric","onset_rel_s":880.8,"rank":4,"service":"paymentservice","severity_z":333.333},{"evidence_source":"metric","onset_rel_s":898.2,"rank":5,"service":"frontend-external","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":903.0,"rank":6,"service":"gke-gke-cluster-default-pool-c49c2b06-d258","severity_z":23.634},{"evidence_source":"metric","onset_rel_s":913.8,"rank":7,"service":"gke-gke-cluster-default-pool-c49c2b06-vlhn","severity_z":18.278},{"evidence_source":"metric","onset_rel_s":922.8,"rank":8,"service":"adservice","severity_z":991.989},{"evidence_source":"metric","onset_rel_s":925.2,"rank":9,"service":"productcatalogservice","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":925.8,"rank":10,"service":"gke-gke-cluster-default-pool-c49c2b06-crhc","severity_z":894.361},{"evidence_source":"metric","onset_rel_s":927.0,"rank":11,"service":"recommendationservice","severity_z":980.08},{"evidence_source":"metric","onset_rel_s":928.2,"rank":12,"service":"cartservice","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":928.2,"rank":13,"service":"currencyservice","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":928.2,"rank":14,"service":"shippingservice","severity_z":124.52}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"currencyservice","caller":"checkoutservice"},{"callee":"emailservice","caller":"checkoutservice"},{"callee":"paymentservice","caller":"checkoutservice"},{"callee":"productcatalogservice","caller":"checkoutservice"},{"callee":"checkoutservice","caller":"frontend"},{"callee":"currencyservice","caller":"frontend"},{"callee":"productcatalogservice","caller":"frontend"},{"callee":"recommendationservice","caller":"frontend"},{"callee":"productcatalogservice","caller":"recommendationservice"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

{"confidence":"high","reason":"Rank checkoutservice first because checkoutservice has direct container-memory-mapped-file evidence (signed-z 999, persistence 13 bins); although frontend is salient, the caller path frontend -> checkoutservice means a disturbance in the callee can propagate back toward that caller-side symptom.","services":["checkoutservice","frontend"]}

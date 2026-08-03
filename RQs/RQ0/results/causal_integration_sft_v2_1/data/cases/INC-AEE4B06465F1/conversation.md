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
opaque_id: INC-AEE4B06465F1
observation_window={"duration_rel_s":1980.0,"source_metric_rows":34}
selection_summary={"candidate_count":60,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":479,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["adservice","adservice-0","adservice-1","adservice-2","cartservice","cartservice-0","cartservice-1","cartservice-2","checkoutservice","checkoutservice-0","checkoutservice-1","checkoutservice-2","currencyservice","currencyservice-0","currencyservice-1","currencyservice-2","emailservice","emailservice-0","emailservice-1","emailservice-2","example-ant-10-29160960-4hv7k","example-ant-29160960-lpx4l","frontend","frontend-0","frontend-1","frontend-2","hipstershop","k8s-master1","k8s-master2","k8s-master3","node-1","node-2","node-3","node-4","node-5","node-6","node-7","node-8","paymentservice","paymentservice-0","paymentservice-1","paymentservice-2","productcatalogservice","productcatalogservice-0","productcatalogservice-1","productcatalogservice-2","recommendationservice","recommendationservice-0","recommendationservice-1","recommendationservice-2","redis","redis-cart","redis-cart-0","shippingservice","shippingservice-0","shippingservice-1","shippingservice-2","tidb-pd","tidb-tidb","tidb-tikv"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[15.469,46.406,77.344,108.281,139.219,170.156,201.094,232.031,262.969,293.906,324.844,355.781,386.719,417.656,448.594,479.531,510.469,541.406,572.344,603.281,634.219,665.156,696.094,727.031,757.969,788.906,819.844,850.781,881.719,912.656,943.594,974.531,1005.469,1036.406,1067.344,1098.281,1129.219,1160.156,1191.094,1222.031,1252.969,1283.906,1314.844,1345.781,1376.719,1407.656,1438.594,1469.531,1500.469,1531.406,1562.344,1593.281,1624.219,1655.156,1686.094,1717.031,1747.969,1778.906,1809.844,1840.781,1871.719,1902.656,1933.594,1964.531]
[M1] rank=1 service=adservice-2 metric=pod_memory_working_set_bytes baseline=54.98 peak=10183709.97 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,934.66,-934.66,0,0,0,0,0,0,10183709.97,-10183709.97,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010101010101010101010101010101001010101010101010101010101010100
observed_counts_compact=csv:1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1
[M2] rank=2 service=cartservice-2 metric=rrt baseline=1378.800588 peak=19078.5 signed_z=92.479 onset_bin=62 onset_rel_s=1933.594 persistence_bins=2
values_compact=delta:1385.88,-259.71,245.6,101.7,534.78,-660.22,70.97,-83.27,-203.35,263.89,-166.52,158.48,-64.5,-117.62,160.04,193.66,-190.93,-51.61,106.42,17654.81,-17664.2,-44.13,244.07,-428.88,140.02,240.41,372.17,-548.24,-49.44,-115.99,-67.61,126.43,16577.21,-9059.11
missing_mask_bits=0010101010101010101010101010101001010101010101010101010101010100
observed_counts_compact=csv:1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1
[M3] rank=3 service=currencyservice-0 metric=rrt_max baseline=4297.529412 peak=72470.0 signed_z=52.128 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:5154,-503,-723,1801,-2822,-26,-169,612,2027,-2074,2261,-2057,4022,-2131,-2350,1850,-1516,494,4480,-4419,5726,-5990,24031,-18283,-6248,-531,1064,4378,-1126,-1070,-2420,-290,69318,-67823
missing_mask_bits=0010101010101010101010101010101001010101010101010101010101010100
observed_counts_compact=csv:1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1
[M4] rank=4 service=cartservice-2 metric=rrt_max baseline=3489.058824 peak=95338.0 signed_z=48.125 onset_bin=62 onset_rel_s=1933.594 persistence_bins=2
values_compact=delta:2662,-686,437,889,6593,-7099,-4,178,-368,1419,-616,-487,-587,-177,803,3797,-3388,-881,305,62225,-62155,157,1287,-2231,980,62,2656,-1668,-347,-1364,-103,1457,91592,-24839
missing_mask_bits=0010101010101010101010101010101001010101010101010101010101010100
observed_counts_compact=csv:1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1
[M5] rank=5 service=currencyservice metric=rrt_max baseline=5734.529412 peak=72470.0 signed_z=30.429 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:10049,-5398,1402,-324,-2482,941,-1476,2357,282,-1151,1338,-2057,4022,-2131,4171,-4671,5057,-6079,4480,-3436,4743,-4464,22505,-18283,-6248,1124,-591,5044,-646,-2216,-2314,453,68469,-67823
missing_mask_bits=0010101010101010101010101010101001010101010101010101010101010100
observed_counts_compact=csv:1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1
[M6] rank=6 service=k8s-master3 metric=node_filesystem_free_bytes baseline=8135420265.411765 peak=8217530368.0 signed_z=20.692 onset_bin=31 onset_rel_s=974.531 persistence_bins=18
values_compact=delta:8133574656,1912832,-77824,0,-20480,16384,970752,-987136,-20480,0,-770048,-1826816,0,0,0,0,17735680,51265536,-2068480,0,0,4096,17772544,-17739776,0,-1040384,0,77824,18751488,-16777216,0,-2031616,0,0
missing_mask_bits=0010101010101010101010101010101001010101010101010101010101010100
observed_counts_compact=csv:1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1
[M7] rank=7 service=cartservice-1 metric=rrt baseline=1764.39 peak=16981.75 signed_z=20.579 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:1494.35,182.92,-213.27,31.18,-158.26,572.54,-502.4,242.99,-128.39,-4.91,143.59,341.34,2640.37,-3047.95,144.15,-255,-80.99,-72.71,262.14,-136.41,79.67,1.72,13.07,-171.78,253.54,-98.27,323.23,-129.65,-374.64,76.41,235.78,-55.92,15373.31,-15336.44
missing_mask_bits=0010101010101010101010101010101001010101010101010101010101010100
observed_counts_compact=csv:1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1
[M8] rank=8 service=emailservice-1 metric=rrt_max baseline=2766.941176 peak=9595.0 signed_z=20.38 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:2572,-54,351,-293,0,371,0,707,-969,-350,-15,628,-565,721,-257,310,-557,200,6795,-6750,-270,182,-317,604,279,-900,290,-104,758,-611,122,459,-225,-344
missing_mask_bits=0010101010101010101010101010101001010101010101010101010101010100
observed_counts_compact=csv:1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1
[M9] rank=9 service=k8s-master3 metric=node_filesystem_usage_rate baseline=68.579412 peak=68.26 signed_z=-20.097 onset_bin=31 onset_rel_s=974.531 persistence_bins=18
values_compact=delta:68.59,-0.01,0,0,0,0,-0.01,0.01,0,0,0,0.01,0,0,0,0,-0.07,-0.2,0.01,0,0,0,-0.07,0.07,0,0,0,0,-0.07,0.07,0,0,0,0
missing_mask_bits=0010101010101010101010101010101001010101010101010101010101010100
observed_counts_compact=csv:1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1
[M10] rank=10 service=currencyservice-2 metric=rrt baseline=1301.495294 peak=3704.38 signed_z=17.208 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:1115,85.4,34.35,-73.08,302.66,54.07,-297.9,-81.56,252.35,-68.12,-6,-51.29,122.54,33.08,-251,436.75,-421,-2.75,-20.92,320.04,-243.62,904.83,-809.47,-46.76,226.23,-257.08,253,2194.63,-2178.58,-42.5,-28.68,72.13,-273.63,445.96
missing_mask_bits=0010101010101010101010101010101001010101010101010101010101010100
observed_counts_compact=csv:1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1
[M11] rank=11 service=currencyservice-2 metric=rrt_max baseline=1826.058824 peak=8724.0 signed_z=14.845 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:1510,158,-33,-22,561,361,-1109,72,374,-281,279,-437,666,-458,-197,1831,-1516,-174,369,369,-668,1959,-1018,-943,912,-1039,1583,5615,-6678,-140,-69,361,-104,1279
missing_mask_bits=0010101010101010101010101010101001010101010101010101010101010100
observed_counts_compact=csv:1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1
[M12] rank=12 service=node-2 metric=node_disk_written_bytes_total baseline=2323.074706 peak=15872.0 signed_z=10.806 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:1092.27,546.13,-546.13,273.06,273.07,273.07,0,-136.54,-682.66,546.13,546.13,853.34,-34.14,2696.54,-853.34,-1945.6,-238.93,13209.6,-12049.07,-375.46,546.13,341.33,-853.33,-136.53,-887.47,1604.27,-1297.07,-921.6,785.07,-921.6,853.33,3720.53,-3618.13,34.13
missing_mask_bits=0010101010101010101010101010101001010101010101010101010101010100
observed_counts_compact=csv:1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[1320.0,1440.0]

=== LOG SUMMARY ===
{"entries":[{"error_logs":5715,"error_pct":14.95,"service":"adservice-0","total_logs":38230},{"error_logs":561,"error_pct":9.93,"service":"frontend-2","total_logs":5651},{"error_logs":444,"error_pct":10.04,"service":"frontend-0","total_logs":4424},{"error_logs":421,"error_pct":9.77,"service":"frontend-1","total_logs":4311},{"error_logs":9,"error_pct":32.14,"service":"adservice-1","total_logs":28},{"error_logs":9,"error_pct":32.14,"service":"adservice-2","total_logs":28}],"mode":"errors","omitted_services":19,"service_count":25}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":-12.0,"error_pct":0.0,"p95_during_ms":0.3777999999999995,"p95_pre_ms":0.42945000000000005,"service":"shippingservice","spans":1190},{"delta_pct":-7.6,"error_pct":0.0,"p95_during_ms":0.8958499999999998,"p95_pre_ms":0.9692999999999999,"service":"emailservice","spans":170},{"delta_pct":-6.6,"error_pct":0.0,"p95_during_ms":3.8063,"p95_pre_ms":4.075299999999999,"service":"cartservice","spans":4028},{"delta_pct":-5.8,"error_pct":0.0,"p95_during_ms":2.4531999999999994,"p95_pre_ms":2.602999999999997,"service":"redis","spans":4364},{"delta_pct":-2.8,"error_pct":0.0,"p95_during_ms":4.760499999999998,"p95_pre_ms":4.89975,"service":"recommendationservice","spans":6034},{"delta_pct":1.4,"error_pct":4.94,"p95_during_ms":90.65539999999999,"p95_pre_ms":89.407,"service":"frontend","spans":49283},{"delta_pct":0.9,"error_pct":0.0,"p95_during_ms":13.82975,"p95_pre_ms":13.702399999999997,"service":"productcatalogservice","spans":22769},{"delta_pct":-0.8,"error_pct":0.0,"p95_during_ms":144.1156999999999,"p95_pre_ms":145.21544999999992,"service":"checkoutservice","spans":2022}],"omitted_services":0,"service_count":8}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=7 omitted_edges=0
[{"evidence_source":"metric","onset_rel_s":1020.0,"rank":1,"service":"k8s-master3","severity_z":20.692},{"evidence_source":"metric","onset_rel_s":1020.0,"rank":2,"service":"node-2","severity_z":10.806},{"evidence_source":"metric","onset_rel_s":1080.0,"rank":3,"service":"emailservice","severity_z":20.38},{"evidence_source":"metric","onset_rel_s":1140.0,"rank":4,"service":"cartservice","severity_z":92.479},{"evidence_source":"metric","onset_rel_s":1380.0,"rank":5,"service":"adservice","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1920.0,"rank":6,"service":"currencyservice","severity_z":52.128},{"evidence_source":"none","onset_rel_s":null,"rank":7,"service":"shippingservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":8,"service":"paymentservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":9,"service":"tidb-pd","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":10,"service":"redis-cart","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":11,"service":"productcatalogservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":12,"service":"checkoutservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":13,"service":"frontend","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":14,"service":"tidb-tidb","severity_z":0.0}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"cartservice","caller":"checkoutservice"},{"callee":"emailservice","caller":"checkoutservice"},{"callee":"productcatalogservice","caller":"checkoutservice"},{"callee":"shippingservice","caller":"checkoutservice"},{"callee":"cartservice","caller":"frontend"},{"callee":"checkoutservice","caller":"frontend"},{"callee":"productcatalogservice","caller":"frontend"},{"callee":"shippingservice","caller":"frontend"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

{"confidence":"medium","reason":"Rank adservice first because adservice has direct pod_memory_working_set_bytes evidence (signed-z 999, persistence 0 bins); k8s-master3 is second despite propagation rank 1 because onset ordering alone does not establish the causal origin. The remaining entries preserve evidence-supported alternatives so the ranking retains calibrated uncertainty instead of collapsing to one answer.","services":["adservice","k8s-master3","node-2","cartservice-2","currencyservice-0"]}

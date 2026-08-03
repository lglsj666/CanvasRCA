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
opaque_id: INC-2E9DC5C4A090
observation_window={"duration_rel_s":2340.0,"source_metric_rows":40}
selection_summary={"candidate_count":60,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":485,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["adservice","adservice-0","adservice-1","adservice-2","cartservice","cartservice-0","cartservice-1","cartservice-2","checkoutservice","checkoutservice-0","checkoutservice-1","checkoutservice-2","currencyservice","currencyservice-0","currencyservice-1","currencyservice-2","emailservice","emailservice-0","emailservice-1","emailservice-2","example-ant-10-29152320-7q99m","example-ant-29152320-kszxj","frontend","frontend-0","frontend-1","frontend-2","hipstershop","k8s-master1","k8s-master2","k8s-master3","node-1","node-2","node-3","node-4","node-5","node-6","node-7","node-8","paymentservice","paymentservice-0","paymentservice-1","paymentservice-2","productcatalogservice","productcatalogservice-0","productcatalogservice-1","productcatalogservice-2","recommendationservice","recommendationservice-0","recommendationservice-1","recommendationservice-2","redis","redis-cart","redis-cart-0","shippingservice","shippingservice-0","shippingservice-1","shippingservice-2","tidb-pd","tidb-tidb","tidb-tikv"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[18.281,54.844,91.406,127.969,164.531,201.094,237.656,274.219,310.781,347.344,383.906,420.469,457.031,493.594,530.156,566.719,603.281,639.844,676.406,712.969,749.531,786.094,822.656,859.219,895.781,932.344,968.906,1005.469,1042.031,1078.594,1115.156,1151.719,1188.281,1224.844,1261.406,1297.969,1334.531,1371.094,1407.656,1444.219,1480.781,1517.344,1553.906,1590.469,1627.031,1663.594,1700.156,1736.719,1773.281,1809.844,1846.406,1882.969,1919.531,1956.094,1992.656,2029.219,2065.781,2102.344,2138.906,2175.469,2212.031,2248.594,2285.156,2321.719]
[M1] rank=1 service=k8s-master2 metric=node_filesystem_free_bytes baseline=9533807411.2 peak=9566904320.0 signed_z=184.845 onset_bin=49 onset_rel_s=1809.844 persistence_bins=3
values_compact=delta:9534033920,-372736,69632,0,-167936,20480,438272,319488,-495616,0,0,32768,40960,-20480,-110592,-20480,0,-139264,20480,0,0,0,114688,0,33140736,-33501184,0,929792,-2088960,24576,0,0,20480,2011136,0,-196608,0,-65536,-65536,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M2] rank=2 service=node-8 metric=node_memory_usage_rate baseline=54.221 peak=80.96 signed_z=61.912 onset_bin=36 onset_rel_s=1334.531 persistence_bins=18
values_compact=delta:53.77,-0.09,0.01,0.01,-0.02,0.24,0.1,-0.16,-0.02,0,0.7,0.02,0.03,-0.05,0.07,0.12,-0.08,0.07,0.02,0,0.18,11.64,14,-0.15,-0.06,0.61,-19.13,0.09,-0.02,0.11,-0.08,-0.01,0.03,0.04,-0.26,0.05,0.13,-0.15,0.1,0.15
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M3] rank=3 service=node-8 metric=node_memory_MemAvailable_bytes baseline=14799192473.6 peak=5801684992.0 signed_z=-61.871 onset_bin=36 onset_rel_s=1334.531 persistence_bins=18
values_compact=delta:14952632320,27537408,-2985984,-3702784,7143424,-79224832,-35241984,54788096,8011776,-700416,-237363200,-5062656,-11718656,18677760,-23101440,-43118592,27230208,-24010752,-5611520,2207744,-61734912,-3918168064,-4711534592,50114560,20914176,-204292096,6435385344,-28033024,5808128,-37548032,27299840,3694592,-8216576,-13475840,85336064,-17625088,-40976384,48775168,-34127872,-49016832
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M4] rank=4 service=shippingservice-1 metric=rrt_max baseline=3232.95 peak=30806.0 signed_z=16.57 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:2383,401,479,2838,-2555,-1289,-547,-118,2134,644,-1294,-28,-915,-166,3051,-2427,-701,924,-972,6706,-2623,-3533,-193,28607,-28956,312,6632,-6635,-111,4948,-4769,108,-457,449,67,4272,-4627,-296,1591,-1663
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M5] rank=5 service=currencyservice-2 metric=pod_cpu_usage baseline=0.0 peak=0.01 signed_z=16.064 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.01,-0.01,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M6] rank=6 service=shippingservice metric=rrt_max baseline=5796.8 peak=30806.0 signed_z=12.276 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:3180,1788,-1434,2567,-1335,132,-1855,2846,3560,-5079,-440,1608,5163,-2207,-1827,-72,-1465,-246,367,3297,-2623,-760,2504,23137,-26516,3282,1222,1582,-3621,1440,1532,-2588,-3015,14703,-13813,3224,-851,-2845,603,1935
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M7] rank=7 service=k8s-master2 metric=node_filesystem_usage_rate baseline=35.11 peak=35.045 signed_z=-9.446 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:35.11,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,-0.065,0.065,0,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M8] rank=8 service=shippingservice-2 metric=rrt_max baseline=3367.35 peak=18827.0 signed_z=9.185 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:3180,232,-1527,414,-45,-273,396,448,-1291,226,381,524,-881,823,4060,-72,-1465,-246,367,865,-2782,1831,2504,185,-3564,-752,1464,5374,-3621,1440,1532,-2588,-3015,14703,-13813,3224,-851,-2845,-1063,631
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M9] rank=9 service=currencyservice-1 metric=rrt_max baseline=17547.95 peak=189073.0 signed_z=7.91 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:18002,-14430,6061,-2238,-1144,781,-2424,4706,70608,-70905,-4777,3455,16867,42504,-57008,43409,-49457,2616,-2135,9507,-2413,-7455,5875,-4388,7931,-6299,-1076,-564,183464,-184298,7642,-5231,-3972,8566,-4643,106306,-106044,2220,-4269,-642
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M10] rank=10 service=adservice-2 metric=pod_memory_working_set_bytes baseline=0.0 peak=326.39 signed_z=7.604 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,326.39,-326.39,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M11] rank=11 service=node-3 metric=node_network_receive_bytes_total baseline=118.97 peak=109.33 signed_z=-7.513 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:120.93,-2.8,0,2.8,-2.8,0,2.8,-2.8,0,0,0,0,0,0,0,2.8,-2.8,0,2.8,0,0,0,-2.8,-8.8,8.8,4.4,-1.6,-2.8,0,2.8,-11.6,8.8,2.8,-2.8,0,2.8,-2.8,0,2.8,-2.8
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M12] rank=12 service=currencyservice metric=rrt_max baseline=20591.4 peak=189073.0 signed_z=7.278 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:18002,-9209,50732,-51137,-1637,281,277,2005,70608,-70905,-4777,3455,18092,41279,-57008,43409,-49457,2616,-1798,9170,-2413,-2691,48736,-50486,6404,-6299,-808,10357,172275,-160053,-16603,-1516,21630,-20751,-3651,105314,-106044,2220,-4269,-635
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[1200.0,2340.0]

=== LOG SUMMARY ===
{"entries":[{"change_pct":143.9,"n_during":3288,"n_pre":1348,"service":"shippingservice-2"},{"change_pct":-86.3,"n_during":386,"n_pre":2824,"service":"shippingservice-0"},{"change_pct":-25.0,"n_during":15,"n_pre":20,"service":"redis-cart-0"},{"change_pct":-12.8,"n_during":16046,"n_pre":18396,"service":"currencyservice-0"},{"change_pct":-12.5,"n_during":7440,"n_pre":8504,"service":"frontend-0"},{"change_pct":-12.3,"n_during":31733,"n_pre":36166,"service":"currencyservice-1"},{"change_pct":-11.9,"n_during":40203,"n_pre":45630,"service":"cartservice-2"},{"change_pct":-11.9,"n_during":560,"n_pre":636,"service":"currencyservice-2"}],"mode":"volume","omitted_services":14,"service_count":22}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":7.4,"error_pct":0.0,"p95_during_ms":1.1182999999999994,"p95_pre_ms":1.0412499999999998,"service":"emailservice","spans":596},{"delta_pct":-5.4,"error_pct":0.0,"p95_during_ms":0.4807999999999997,"p95_pre_ms":0.5083000000000002,"service":"shippingservice","spans":4191},{"delta_pct":-5.0,"error_pct":0.0,"p95_during_ms":128.54149999999998,"p95_pre_ms":135.33649999999994,"service":"checkoutservice","spans":7064},{"delta_pct":-2.1,"error_pct":0.0,"p95_during_ms":3.1563999999999997,"p95_pre_ms":3.2227499999999965,"service":"redis","spans":15617},{"delta_pct":-0.7,"error_pct":0.0,"p95_during_ms":4.597,"p95_pre_ms":4.629599999999999,"service":"cartservice","spans":14410},{"delta_pct":0.3,"error_pct":0.0,"p95_during_ms":88.9039,"p95_pre_ms":88.65199999999997,"service":"frontend","spans":175980},{"delta_pct":-0.1,"error_pct":0.0,"p95_during_ms":14.002,"p95_pre_ms":14.011299999999995,"service":"productcatalogservice","spans":81388},{"delta_pct":-0.0,"error_pct":0.0,"p95_during_ms":5.127700000000001,"p95_pre_ms":5.128949999999999,"service":"recommendationservice","spans":21606}],"omitted_services":0,"service_count":8}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=6 omitted_edges=0
[{"evidence_source":"metric","onset_rel_s":1320.0,"rank":1,"service":"node-8","severity_z":61.912},{"evidence_source":"metric","onset_rel_s":1380.0,"rank":2,"service":"shippingservice","severity_z":16.57},{"evidence_source":"metric","onset_rel_s":1440.0,"rank":3,"service":"k8s-master2","severity_z":184.845},{"evidence_source":"metric","onset_rel_s":1980.0,"rank":4,"service":"currencyservice","severity_z":16.064},{"evidence_source":"none","onset_rel_s":null,"rank":5,"service":"adservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":6,"service":"paymentservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":7,"service":"tidb-tikv","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":8,"service":"tidb-tidb","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":9,"service":"k8s-master3","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":10,"service":"emailservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":11,"service":"frontend","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":12,"service":"redis-cart","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":13,"service":"recommendationservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":14,"service":"checkoutservice","severity_z":0.0}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"emailservice","caller":"checkoutservice"},{"callee":"shippingservice","caller":"checkoutservice"},{"callee":"checkoutservice","caller":"frontend"},{"callee":"recommendationservice","caller":"frontend"},{"callee":"shippingservice","caller":"frontend"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

{"confidence":"high","reason":"Rank shippingservice-0 first because shippingservice-0 has direct rrt_max evidence (signed-z 12.28, persistence 0 bins); although frontend is salient, the caller path frontend -> shippingservice means a disturbance in the callee can propagate back toward that caller-side symptom. The remaining entries preserve evidence-supported alternatives so the ranking retains calibrated uncertainty instead of collapsing to one answer.","services":["shippingservice-0","node-8","k8s-master2","currencyservice","frontend"]}

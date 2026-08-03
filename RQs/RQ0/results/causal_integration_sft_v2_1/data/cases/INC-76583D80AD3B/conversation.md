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
opaque_id: INC-76583D80AD3B
observation_window={"duration_rel_s":2340.0,"source_metric_rows":40}
selection_summary={"candidate_count":63,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":1285,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["adservice","adservice-0","adservice-1","adservice-2","adservice-grpc","adservice-http","adservice2","adservice2-0","cartservice-0","cartservice-1","cartservice-2","cartservice-grpc","cartservice2-0","checkoutservice-0","checkoutservice-1","checkoutservice-2","checkoutservice-grpc","checkoutservice2-0","currencyservice-0","currencyservice-1","currencyservice-2","currencyservice-grpc","currencyservice2-0","emailservice-0","emailservice-1","emailservice-2","emailservice-grpc","emailservice2-0","frontend-0","frontend-1","frontend-2","frontend-http","frontend2-0","istio-egressgateway-7bfdcc9d86-zpjpg","istio-ingressgateway-565bffd4d-6bl7m","node-1","node-2","node-3","node-4","node-5","node-6","paymentservice-0","paymentservice-1","paymentservice-2","paymentservice-grpc","paymentservice2-0","productcatalogservice-0","productcatalogservice-1","productcatalogservice-2","productcatalogservice-grpc","productcatalogservice2-0","recommendationservice-0","recommendationservice-1","recommendationservice-2","recommendationservice-grpc","recommendationservice2-0","redis-cart-0","redis-cart2-0","shippingservice-0","shippingservice-1","shippingservice-2","shippingservice-grpc","shippingservice2-0"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[18.281,54.844,91.406,127.969,164.531,201.094,237.656,274.219,310.781,347.344,383.906,420.469,457.031,493.594,530.156,566.719,603.281,639.844,676.406,712.969,749.531,786.094,822.656,859.219,895.781,932.344,968.906,1005.469,1042.031,1078.594,1115.156,1151.719,1188.281,1224.844,1261.406,1297.969,1334.531,1371.094,1407.656,1444.219,1480.781,1517.344,1553.906,1590.469,1627.031,1663.594,1700.156,1736.719,1773.281,1809.844,1846.406,1882.969,1919.531,1956.094,1992.656,2029.219,2065.781,2102.344,2138.906,2175.469,2212.031,2248.594,2285.156,2321.719]
[M1] rank=1 service=adservice metric=jvm_threads_started baseline=0.0 peak=0.5 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.5,0,-0.5,0,0,0,0,0,0,0,0,0,0,0,0,0.5,0,-0.5,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M2] rank=2 service=node-2 metric=system.disk.pct_usage baseline=41.45 peak=41.46 signed_z=999.0 onset_bin=44 onset_rel_s=1627.031 persistence_bins=2
values_compact=delta:41.45,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.01,0,0,-0.01,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M3] rank=3 service=node-6 metric=system.disk.free baseline=1416654737.067 peak=2030399488.0 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:1416978090.67,-15872,-28330.67,37120,-36608,-31146.67,-14933.33,-19029.33,26880,-16384,-557482.67,-12800,-18346.67,22784,-22698.66,-22357.34,-20394.66,7765.33,546901.33,-29781.33,40789.33,-9130.66,18346.66,-37717.33,613613824,-613721514.67,-93952,-81920,-9472,820394.67,165034.67,-8106.67,-22954.67,-48042.66,-12032,20224,-13738.67,-13397.33,-20821.34,-42496
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M4] rank=4 service=node-6 metric=system.disk.total baseline=5101719893.33 peak=8303560996.57 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:5101719893.33,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,3201841103.24,-3201841103.24,0,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M5] rank=5 service=node-6 metric=system.disk.used baseline=3663929907.2 peak=6255045485.71 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:3663606784,15360,28672,-37205.33,36522.66,31402.67,14677.33,19114.67,-26965.33,16725.33,557056,12970.67,18432,-22869.34,22528,22528,20480,-7509.33,-547157.33,29696,-40960,9216,-18432,37546.66,2591246872.38,-2591138669.71,93866.67,81920,9557.33,-820906.67,-164864,8192,22869.34,48469.33,11946.67,-20480,13994.66,13312,20821.34,42666.66
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M6] rank=6 service=node-6 metric=system.fs.inodes.free baseline=3841189990.4005 peak=6556195693.71 signed_z=999.0 onset_bin=41 onset_rel_s=1517.344 persistence_bins=15
values_compact=delta:3841594368,-69632,-83968,141994.67,-151210.67,-98304,-65877.33,-84992,162133.33,-75093.33,-151893.34,-57685.33,-79530.67,119466.67,-96597.33,-94549.34,-54613.33,22528,133120,-90453.33,-5461.34,-41642.66,99328,-159402.67,2715383661.71,-2715778243.04,-381952,-300032,-45056,3275776,686080,-38570.67,-101034.67,-162133.33,-56661.33,109226.66,-63488,-59733.33,-57344,-175445.33
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M7] rank=7 service=node-6 metric=system.fs.inodes.in_use baseline=1.17 peak=1.01 signed_z=-999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:1.17,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,-0.16,0.16,0,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M8] rank=8 service=node-6 metric=system.fs.inodes.total baseline=3842762478.934 peak=6558498816.0 signed_z=999.0 onset_bin=41 onset_rel_s=1517.344 persistence_bins=15
values_compact=delta:3843166549.33,-69290.66,-83968,141994.66,-151210.66,-98304,-65877.34,-84992,162133.34,-75093.34,-151893.33,-57685.33,-79530.67,119466.67,-96938.67,-94208,-54613.33,22528,133120,-90453.34,-5461.33,-41642.67,99328,-159402.66,2716114261.33,-2716508842.67,-381610.66,-300032,-45056,3275776,685738.66,-38570.66,-100693.34,-162474.66,-56661.34,109226.67,-63488,-59733.33,-57002.67,-175786.67
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M9] rank=9 service=node-6 metric=system.fs.inodes.used baseline=1572463.9005 peak=2302529.14 signed_z=999.0 onset_bin=41 onset_rel_s=1517.344 persistence_bins=15
values_compact=delta:1572466,-1.33,-4.34,3.84,-8.84,12,-6.16,1,-3.5,6.5,4,-11.67,7.33,3.5,-6,-0.33,1.17,10.83,-11.5,6.67,0,-4.5,8.16,-2,730058.31,-729789.97,16.66,-20,7.17,-88.83,-30.17,-7.5,7.33,-6.83,11.33,-11.33,10.83,-9,-6.5,10.67
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M10] rank=10 service=emailservice-2 metric=container_network_receive_MB.eth0 baseline=0.025043 peak=0.640156 signed_z=357.949 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.026882,-0.005245,0.004993,-0.001185,-0.001662,0.002109,-0.002048,0.001521,-0.00065,-0.001369,0.00272,-0.003603,0.003854,-0.002906,0.00301,0.000499,0.001489,-0.00497,0.002765,-0.00254,0.002518,-0.002645,0.000176,0.001451,0.614992,0,-0.614285,-0.002086,0.001903,-0.000654,-0.00341,0.005575,-0.005161,0.004503,-0.00321,0.003762,-0.002857,0.002933,-0.001168,0.000129
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M11] rank=11 service=paymentservice-0 metric=container_network_receive_MB.eth0 baseline=0.022319 peak=0.598945 signed_z=340.141 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.019295,0.00321,0.000056,0.000125,0.000993,-0.002696,0.002217,-0.003036,0.005831,-0.005324,0.002817,0.000678,-0.00331,-0.000406,0.003982,-0.004279,0.00194,0.00146,-0.001648,0.001642,-0.004827,0.002551,0.000614,0.000422,-0.003471,0,0.006187,-0.005549,0.004836,0.574635,-0.576691,0.000152,-0.002339,0.002745,-0.000785,-0.001851,0.0031,0.002555,-0.003593,0.001741
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M12] rank=12 service=node-1 metric=system.mem.free baseline=2015.6 peak=21016.0 signed_z=254.164 onset_bin=41 onset_rel_s=1517.344 persistence_bins=6
values_compact=delta:2116,-119,1,-13,2,48,-12,2,-10,0,-6,-16,-7,319,-310,-25,14,-30,-1,14,11,-38,20,-13,-1,19070,-18419,-134,-286,14,-9,122,-54,-66,-59,355,-302,19,-68,-48
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[1500.0,1740.0]

=== LOG SUMMARY ===
{"entries":[{"change_pct":-100.0,"n_during":0,"n_pre":34,"service":"redis-cart-0"},{"change_pct":-92.1,"n_during":15,"n_pre":190,"service":"paymentservice-1"},{"change_pct":-91.9,"n_during":85,"n_pre":1052,"service":"checkoutservice-2"},{"change_pct":-89.6,"n_during":19,"n_pre":183,"service":"emailservice-1"},{"change_pct":-89.4,"n_during":19,"n_pre":179,"service":"emailservice-2"},{"change_pct":-89.4,"n_during":20,"n_pre":189,"service":"paymentservice-0"},{"change_pct":-89.2,"n_during":179,"n_pre":1663,"service":"shippingservice-2"},{"change_pct":-89.0,"n_during":1389,"n_pre":12590,"service":"currencyservice-0"}],"mode":"volume","omitted_services":23,"service_count":31}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":-98.8,"error_pct":0.0,"p95_during_ms":5.771,"p95_pre_ms":499.69875,"service":"productcatalogservice-0","spans":9097},{"delta_pct":-20.7,"error_pct":0.0,"p95_during_ms":0.018249999999999985,"p95_pre_ms":0.023,"service":"adservice-2","spans":1002},{"delta_pct":20.6,"error_pct":0.0,"p95_during_ms":0.09359999999999988,"p95_pre_ms":0.07759999999999996,"service":"shippingservice-2","spans":476},{"delta_pct":-14.8,"error_pct":0.0,"p95_during_ms":3.01625,"p95_pre_ms":3.5416999999999907,"service":"recommendationservice-2","spans":2416},{"delta_pct":-13.7,"error_pct":0.0,"p95_during_ms":0.1706,"p95_pre_ms":0.19765,"service":"paymentservice-1","spans":67},{"delta_pct":-11.7,"error_pct":0.0,"p95_during_ms":44.36345,"p95_pre_ms":50.22239999999999,"service":"checkoutservice-0","spans":792},{"delta_pct":-10.2,"error_pct":0.0,"p95_during_ms":3.0475000000000003,"p95_pre_ms":3.3934000000000033,"service":"recommendationservice-1","spans":2414},{"delta_pct":-9.8,"error_pct":0.0,"p95_during_ms":0.15595,"p95_pre_ms":0.17289999999999997,"service":"paymentservice-2","spans":66}],"omitted_services":22,"service_count":30}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=16 omitted_edges=1
[{"evidence_source":"metric","onset_rel_s":1200.0,"rank":1,"service":"adservice","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1200.0,"rank":2,"service":"redis-cart2","severity_z":250.947},{"evidence_source":"metric","onset_rel_s":1200.0,"rank":3,"service":"cartservice2","severity_z":144.13},{"evidence_source":"metric","onset_rel_s":1260.0,"rank":4,"service":"cartservice","severity_z":126.47},{"evidence_source":"metric","onset_rel_s":1260.0,"rank":5,"service":"frontend","severity_z":88.41},{"evidence_source":"metric","onset_rel_s":1440.0,"rank":6,"service":"node-6","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1440.0,"rank":7,"service":"emailservice","severity_z":357.949},{"evidence_source":"metric","onset_rel_s":1440.0,"rank":8,"service":"productcatalogservice","severity_z":210.833},{"evidence_source":"metric","onset_rel_s":1500.0,"rank":9,"service":"node-1","severity_z":254.164},{"evidence_source":"metric","onset_rel_s":1560.0,"rank":10,"service":"node-2","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1740.0,"rank":11,"service":"shippingservice","severity_z":170.769},{"evidence_source":"metric","onset_rel_s":1740.0,"rank":12,"service":"node-3","severity_z":124.337},{"evidence_source":"metric","onset_rel_s":1800.0,"rank":13,"service":"node-4","severity_z":122.701},{"evidence_source":"trace","onset_rel_s":2315.4,"rank":14,"service":"paymentservice","severity_z":4.191}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"adservice","caller":"frontend"},{"callee":"cartservice","caller":"frontend"},{"callee":"productcatalogservice","caller":"frontend"},{"callee":"shippingservice","caller":"frontend"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

{"confidence":"high","reason":"Rank productcatalogservice-0 first because productcatalogservice-0 has direct trace evidence; although frontend-0 is salient, the caller path frontend -> productcatalogservice means a disturbance in the callee can propagate back toward that caller-side symptom. The remaining entries preserve evidence-supported alternatives so the ranking retains calibrated uncertainty instead of collapsing to one answer.","services":["productcatalogservice-0","node-6","node-1","node-2","frontend-0"]}

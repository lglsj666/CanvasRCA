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
opaque_id: INC-E291854EB1DB
observation_window={"duration_rel_s":2160.0,"source_metric_rows":37}
selection_summary={"candidate_count":60,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":522,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["adservice","adservice-0","adservice-1","adservice-2","cartservice","cartservice-0","cartservice-1","cartservice-2","checkoutservice","checkoutservice-0","checkoutservice-1","checkoutservice-2","currencyservice","currencyservice-0","currencyservice-1","currencyservice-2","emailservice","emailservice-0","emailservice-1","emailservice-2","example-ant-10-29162400-r2drh","example-ant-29162400-cdnr4","frontend","frontend-0","frontend-1","frontend-2","hipstershop","k8s-master1","k8s-master2","k8s-master3","node-1","node-2","node-3","node-4","node-5","node-6","node-7","node-8","paymentservice","paymentservice-0","paymentservice-1","paymentservice-2","productcatalogservice","productcatalogservice-0","productcatalogservice-1","productcatalogservice-2","recommendationservice","recommendationservice-0","recommendationservice-1","recommendationservice-2","redis","redis-cart","redis-cart-0","shippingservice","shippingservice-0","shippingservice-1","shippingservice-2","tidb-pd","tidb-tidb","tidb-tikv"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[16.875,50.625,84.375,118.125,151.875,185.625,219.375,253.125,286.875,320.625,354.375,388.125,421.875,455.625,489.375,523.125,556.875,590.625,624.375,658.125,691.875,725.625,759.375,793.125,826.875,860.625,894.375,928.125,961.875,995.625,1029.375,1063.125,1096.875,1130.625,1164.375,1198.125,1231.875,1265.625,1299.375,1333.125,1366.875,1400.625,1434.375,1468.125,1501.875,1535.625,1569.375,1603.125,1636.875,1670.625,1704.375,1738.125,1771.875,1805.625,1839.375,1873.125,1906.875,1940.625,1974.375,2008.125,2041.875,2075.625,2109.375,2143.125]
[M1] rank=1 service=adservice-1 metric=pod_cpu_usage baseline=0.01 peak=0.02 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.01,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.01,-0.01,0,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010101001010101001010100101010100101010010101010010101001010100
observed_counts_compact=csv:1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1
[M2] rank=2 service=k8s-master2 metric=node_filesystem_usage_rate baseline=35.17 peak=35.14 signed_z=-999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:35.17,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.005,-0.005,-0.03,0.03,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010101001010101001010100101010100101010010101010010101001010100
observed_counts_compact=csv:1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1
[M3] rank=3 service=node-3 metric=node_network_transmit_bytes_total baseline=3519.992222 peak=3597.4 signed_z=50.131 onset_bin=48 onset_rel_s=1636.875 persistence_bins=10
values_compact=delta:3518.93,0.07,-0.53,1.86,0.67,0.8,-2.73,0.86,0.94,-1.34,1.47,-0.27,-3.13,5,-0.27,-5.86,4,-0.74,-0.46,5.13,-5.87,-1.13,3.07,38.06,-2.33,0,-1.07,1.14,-0.47,-1.13,-0.14,1.8,1.74,-1.8,35.73,5.4,-6.47
missing_mask_bits=0010101001010101001010100101010100101010010101010010101001010100
observed_counts_compact=csv:1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1
[M4] rank=4 service=k8s-master2 metric=node_filesystem_free_bytes baseline=9501513955.555555 peak=9518002176.0 signed_z=44.014 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:9501831168,-258048,0,0,0,0,0,0,0,-65536,958464,-1024000,0,0,512000,-1077248,-24576,0,-20480,20480,17149952,-16613376,86016,0,20480,-20480,20480,-385024,40960,0,0,-16384,1257472,-995328,-237568,0,-8192
missing_mask_bits=0010101001010101001010100101010100101010010101010010101001010100
observed_counts_compact=csv:1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1
[M5] rank=5 service=node-4 metric=node_network_transmit_bytes_total baseline=3408.95 peak=3453.53 signed_z=20.426 onset_bin=48 onset_rel_s=1636.875 persistence_bins=10
values_compact=delta:3410.8,3.2,-6.27,0.54,-0.02,0.02,-1.74,1.87,0.73,-1.26,0.26,-1.93,5.87,0.46,-7.2,3.39,1.75,-2.07,0.53,0.54,-0.87,0.07,-3.27,44.4,3.73,-2,-1.46,-1.67,1.2,-0.8,2.6,-2.07,-3.33,5.87,-5.14,0.27,3.6
missing_mask_bits=0010101001010101001010100101010100101010010101010010101001010100
observed_counts_compact=csv:1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1
[M6] rank=6 service=node-4 metric=node_memory_MemAvailable_bytes baseline=9135277624.88889 peak=11863416832.0 signed_z=12.661 onset_bin=39 onset_rel_s=1333.125 persistence_bins=15
values_compact=delta:9428545536,-6533120,-1208320,-146206720,-230019072,-20254720,15593472,393330688,-349016064,4259840,-9658368,223170560,5537792,-516034560,-12587008,-2420736,301510656,-17076224,-194592768,-712142848,-240435200,-18825216,10412032,-40349696,-14991360,-651870208,-76148736,925696,22044672,4699185152,8929280,9601024,741376,-330407936,-28487680,-59785216,5468160
missing_mask_bits=0010101001010101001010100101010100101010010101010010101001010100
observed_counts_compact=csv:1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1
[M7] rank=7 service=node-4 metric=node_memory_usage_rate baseline=43.201667 peak=26.96 signed_z=-12.637 onset_bin=39 onset_rel_s=1333.125 persistence_bins=15
values_compact=delta:41.45,0.04,0.01,0.87,1.37,0.12,-0.09,-2.35,2.09,-0.03,0.06,-1.33,-0.03,3.07,0.08,0.01,-1.8,0.11,1.16,4.24,1.44,0.11,-0.06,0.24,0.09,3.88,0.47,0,-0.13,-28.02,-0.05,-0.06,0,1.97,0.17,0.36,-0.03
missing_mask_bits=0010101001010101001010100101010100101010010101010010101001010100
observed_counts_compact=csv:1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1
[M8] rank=8 service=redis-cart-0 metric=pod_fs_writes_bytes baseline=31048.230556 peak=1183327.41 signed_z=9.001 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,558868.15,-558868.15,0,0,0,0,0,0,0,0,0,0,0,0,0,0,715491.31,-715491.31,0,0,0,1183327.41,-1183327.41,0,0,0,0,0,0,0
missing_mask_bits=0010101001010101001010100101010100101010010101010010101001010100
observed_counts_compact=csv:1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1
[M9] rank=9 service=node-6 metric=node_disk_read_bytes_total baseline=0.0 peak=546.13 signed_z=8.812 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,546.13,-546.13,0,0,0,0,0,0,0,273.07
missing_mask_bits=0010101001010101001010100101010100101010010101010010101001010100
observed_counts_compact=csv:1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1
[M10] rank=10 service=node-1 metric=node_disk_write_time_seconds_total baseline=0.0 peak=0.01 signed_z=8.731 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.01,-0.01,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010101001010101001010100101010100101010010101010010101001010100
observed_counts_compact=csv:1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1
[M11] rank=11 service=node-8 metric=node_disk_write_time_seconds_total baseline=0.0 peak=0.01 signed_z=8.731 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.01,-0.01,0,0,0,0,0,0,0,0,0,0,0,0,0.01,-0.01,0
missing_mask_bits=0010101001010101001010100101010100101010010101010010101001010100
observed_counts_compact=csv:1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1
[M12] rank=12 service=node-7 metric=node_disk_written_bytes_total baseline=43939.082222 peak=174899.2 signed_z=8.653 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:50517.33,-17851.73,26248.53,3618.14,-8499.2,-3481.6,-14745.6,-7031.47,-4437.33,-307.2,43758.93,-18670.93,-5632,-14370.14,-12014.93,51438.93,-20445.86,-2594.14,26419.2,-28876.8,-5939.2,-477.86,26862.93,-19797.33,5529.6,46899.2,78779.73,-114995.2,-7099.73,31709.86,-21708.8,13482.67,2901.33,-1092.26,-19387.74,819.2,34679.47
missing_mask_bits=0010101001010101001010100101010100101010010101010010101001010100
observed_counts_compact=csv:1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[1320.0,2160.0]

=== LOG SUMMARY ===
{"entries":[{"error_logs":1086,"error_pct":4.52,"service":"frontend-1","total_logs":24027},{"error_logs":731,"error_pct":4.7,"service":"frontend-0","total_logs":15560},{"error_logs":678,"error_pct":4.52,"service":"frontend-2","total_logs":15009},{"error_logs":2,"error_pct":50.0,"service":"adservice-0","total_logs":4}],"mode":"errors","omitted_services":20,"service_count":24}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":-45.7,"error_pct":0.0,"p95_during_ms":56.062099999999944,"p95_pre_ms":103.16579999999954,"service":"checkoutservice","spans":5953},{"delta_pct":-15.1,"error_pct":0.0,"p95_during_ms":67.6300999999998,"p95_pre_ms":79.68999999999997,"service":"frontend","spans":186102},{"delta_pct":2.4,"error_pct":0.0,"p95_during_ms":5.4094999999999995,"p95_pre_ms":5.283049999999999,"service":"recommendationservice","spans":23596},{"delta_pct":2.0,"error_pct":0.0,"p95_during_ms":3.021,"p95_pre_ms":2.962899999999998,"service":"redis","spans":17069},{"delta_pct":0.6,"error_pct":0.0,"p95_during_ms":13.984,"p95_pre_ms":13.893899999999995,"service":"productcatalogservice","spans":85462},{"delta_pct":-0.4,"error_pct":0.0,"p95_during_ms":4.752799999999999,"p95_pre_ms":4.769950000000002,"service":"cartservice","spans":15817},{"delta_pct":null,"error_pct":0.0,"p95_during_ms":null,"p95_pre_ms":1.0797499999999998,"service":"emailservice","spans":274},{"delta_pct":null,"error_pct":0.0,"p95_during_ms":null,"p95_pre_ms":0.44025000000000003,"service":"shippingservice","spans":1916}],"omitted_services":0,"service_count":8}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=7 omitted_edges=0
[{"evidence_source":"metric","onset_rel_s":1200.0,"rank":1,"service":"k8s-master2","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1260.0,"rank":2,"service":"adservice","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1380.0,"rank":3,"service":"node-4","severity_z":20.426},{"evidence_source":"metric","onset_rel_s":2040.0,"rank":4,"service":"node-3","severity_z":50.131},{"evidence_source":"none","onset_rel_s":null,"rank":5,"service":"redis-cart","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":6,"service":"currencyservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":7,"service":"frontend","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":8,"service":"checkoutservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":9,"service":"k8s-master3","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":10,"service":"tidb-tikv","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":11,"service":"tidb-tidb","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":12,"service":"example-ant","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":13,"service":"paymentservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":14,"service":"shippingservice","severity_z":0.0}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"shippingservice","caller":"checkoutservice"},{"callee":"checkoutservice","caller":"frontend"},{"callee":"shippingservice","caller":"frontend"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

{"confidence":"high","reason":"Rank shippingservice first because shippingservice has direct trace evidence; although frontend is salient, the caller path frontend -> shippingservice means a disturbance in the callee can propagate back toward that caller-side symptom.","services":["shippingservice","frontend"]}

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
opaque_id: INC-D565F4F5361D
observation_window={"duration_rel_s":1980.0,"source_metric_rows":34}
selection_summary={"candidate_count":60,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":497,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["adservice","adservice-0","adservice-1","adservice-2","cartservice","cartservice-0","cartservice-1","cartservice-2","checkoutservice","checkoutservice-0","checkoutservice-1","checkoutservice-2","currencyservice","currencyservice-0","currencyservice-1","currencyservice-2","emailservice","emailservice-0","emailservice-1","emailservice-2","example-ant-10-29159520-nlwlw","example-ant-29159520-w5hmd","frontend","frontend-0","frontend-1","frontend-2","hipstershop","k8s-master1","k8s-master2","k8s-master3","node-1","node-2","node-3","node-4","node-5","node-6","node-7","node-8","paymentservice","paymentservice-0","paymentservice-1","paymentservice-2","productcatalogservice","productcatalogservice-0","productcatalogservice-1","productcatalogservice-2","recommendationservice","recommendationservice-0","recommendationservice-1","recommendationservice-2","redis","redis-cart","redis-cart-0","shippingservice","shippingservice-0","shippingservice-1","shippingservice-2","tidb-pd","tidb-tidb","tidb-tikv"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[15.469,46.406,77.344,108.281,139.219,170.156,201.094,232.031,262.969,293.906,324.844,355.781,386.719,417.656,448.594,479.531,510.469,541.406,572.344,603.281,634.219,665.156,696.094,727.031,757.969,788.906,819.844,850.781,881.719,912.656,943.594,974.531,1005.469,1036.406,1067.344,1098.281,1129.219,1160.156,1191.094,1222.031,1252.969,1283.906,1314.844,1345.781,1376.719,1407.656,1438.594,1469.531,1500.469,1531.406,1562.344,1593.281,1624.219,1655.156,1686.094,1717.031,1747.969,1778.906,1809.844,1840.781,1871.719,1902.656,1933.594,1964.531]
[M1] rank=1 service=currencyservice-2 metric=pod_memory_working_set_bytes baseline=1458.875882 peak=1279433.99 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:836.29,229.39,-418.19,1680.44,-773.34,335.8,-490.3,-516.64,597.96,-166.56,-247.7,104.48,702.7,-848.88,1686.1,-2245.54,2616.59,-2628.15,1848.89,-1730,463.34,640.92,-387.01,-338.38,143.94,1112.93,1134441.07,142783.84,-1279205.81,82.48,-33.43,-277.23,230.67,308.88
missing_mask_bits=0010101010101010101010101010101001010101010101010101010101010100
observed_counts_compact=csv:1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1
[M2] rank=2 service=example-ant-29159520-w5hmd metric=pod_network_receive_bytes baseline=9.761765 peak=6986.17 signed_z=999.0 onset_bin=62 onset_rel_s=1933.594 persistence_bins=2
values_compact=delta:10.83,-1.26,0.47,3.61,0.12,-9.74,6.79,-4,6.69,-2.68,-6.68,0.66,10.32,-5.94,-0.31,2.27,-2.38,-3.27,5.32,2.22,-1.2,-3.3,-2.9,1.32,-6.96,10.36,-10.36,8.11,553.78,2034.51,120.98,4268.79,-1915.69,-2222.38
missing_mask_bits=0010101010101010101010101010101001010101010101010101010101010100
observed_counts_compact=csv:1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1
[M3] rank=3 service=tidb-tikv metric=raft_propose_wait baseline=0.0 peak=0.01 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.01,-0.01,0,0,0
missing_mask_bits=0010101010101010101010101010101001010101010101010101010101010100
observed_counts_compact=csv:1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1
[M4] rank=4 service=k8s-master2 metric=node_filesystem_free_bytes baseline=9538879488.0 peak=9572835328.0 signed_z=146.199 onset_bin=62 onset_rel_s=1933.594 persistence_bins=2
values_compact=delta:9539194880,0,0,-241664,0,0,-65536,0,229376,0,-249856,-299008,0,0,0,212992,-204800,1118208,0,0,-212992,33353728,-33771520,-45056,0,0,0,33468416,217088,-262144,-65536,-20480,73728,151552
missing_mask_bits=0010101010101010101010101010101001010101010101010101010101010100
observed_counts_compact=csv:1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1
[M5] rank=5 service=example-ant-29159520-w5hmd metric=pod_network_transmit_bytes baseline=9.761765 peak=321.81 signed_z=96.138 onset_bin=62 onset_rel_s=1933.594 persistence_bins=2
values_compact=delta:10.83,-1.26,0.47,3.61,0.12,-9.74,6.79,-4,6.69,-2.68,-6.68,0.66,10.32,-5.94,-0.31,2.27,-2.38,-3.27,5.32,2.22,-1.2,-3.3,-2.9,1.32,-6.96,10.36,-10.36,8.11,22.76,116.76,-7.36,181.54,-75.42,-106.99
missing_mask_bits=0010101010101010101010101010101001010101010101010101010101010100
observed_counts_compact=csv:1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1
[M6] rank=6 service=example-ant-29159520-w5hmd metric=pod_network_receive_packets baseline=0.172941 peak=2.62 signed_z=36.183 onset_bin=62 onset_rel_s=1933.594 persistence_bins=2
values_compact=delta:0.19,-0.04,0,0.12,0.01,-0.22,0.14,-0.1,0.15,-0.05,-0.1,-0.03,0.21,-0.11,-0.02,0.04,-0.06,-0.05,0.11,0.05,-0.04,-0.07,-0.04,0.04,-0.13,0.17,-0.17,0.15,0.12,0.82,0.16,1.37,-0.56,-0.94
missing_mask_bits=0010101010101010101010101010101001010101010101010101010101010100
observed_counts_compact=csv:1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1
[M7] rank=7 service=example-ant-29159520-w5hmd metric=pod_network_transmit_packets baseline=0.172941 peak=2.62 signed_z=36.183 onset_bin=62 onset_rel_s=1933.594 persistence_bins=2
values_compact=delta:0.19,-0.04,0,0.12,0.01,-0.22,0.14,-0.1,0.15,-0.05,-0.1,-0.03,0.21,-0.11,-0.02,0.04,-0.06,-0.05,0.11,0.05,-0.04,-0.07,-0.04,0.04,-0.13,0.17,-0.17,0.15,0.12,0.82,-0.09,1.62,-0.74,-0.76
missing_mask_bits=0010101010101010101010101010101001010101010101010101010101010100
observed_counts_compact=csv:1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1
[M8] rank=8 service=shippingservice-0 metric=rrt_max baseline=3430.588235 peak=49128.0 signed_z=30.556 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:2450,-351,1235,979,-2117,81,2558,-278,3617,-5462,440,950,-688,-1112,1559,-994,-1192,3678,-3184,1498,-195,-1775,7810,-2935,-2264,-1587,-11,-164,46582,-46484,-226,-620,2495,6108
missing_mask_bits=0010101010101010101010101010101001010101010101010101010101010100
observed_counts_compact=csv:1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1
[M9] rank=9 service=shippingservice metric=rrt_max baseline=3725.882353 peak=49128.0 signed_z=26.861 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:2450,-351,3805,-1591,-2117,81,2558,-278,3617,-5462,440,950,1762,-3562,1559,-994,-1192,3678,-3184,1498,-195,-660,6695,-2935,-2264,-1587,-11,-164,46582,-46484,-226,-620,2495,6108
missing_mask_bits=0010101010101010101010101010101001010101010101010101010101010100
observed_counts_compact=csv:1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1
[M10] rank=10 service=node-6 metric=node_memory_usage_rate baseline=27.329412 peak=20.32 signed_z=-26.3 onset_bin=62 onset_rel_s=1933.594 persistence_bins=2
values_compact=delta:27.15,0.27,0.17,-0.04,-0.53,-0.06,0.18,0.1,-0.03,-0.18,-0.03,0.78,0.01,-0.52,0.02,0.2,0.18,-0.02,-0.46,0.06,0.11,0.12,-0.02,-0.08,0.04,-0.05,-7.05,0.03,0.08,-0.04,0.08,0.22,0.01,-0.02
missing_mask_bits=0010101010101010101010101010101001010101010101010101010101010100
observed_counts_compact=csv:1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1
[M11] rank=11 service=node-6 metric=node_memory_MemAvailable_bytes baseline=24307425039.058823 peak=26664902656.0 signed_z=26.243 onset_bin=62 onset_rel_s=1933.594 persistence_bins=2
values_compact=delta:24366272512,-88907776,-56922112,13484032,176013312,21323776,-59707392,-32854016,10080256,60100608,10215424,-264237056,-3911680,177209344,-8798208,-64651264,-62758912,6496256,156811264,-21024768,-37232640,-39645184,6062080,26595328,-13287424,15466496,2372710400,-8892416,-28348416,14958592,-26886144,-73293824,-2641920,6848512
missing_mask_bits=0010101010101010101010101010101001010101010101010101010101010100
observed_counts_compact=csv:1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1
[M12] rank=12 service=redis-cart-0 metric=timeout baseline=0.0 peak=1.0 signed_z=15.6 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,-1,0,1,-1,0,0,0,1,-1,1,-1
missing_mask_bits=0010101010101010101010101010101001010101010101010101010101010100
observed_counts_compact=csv:1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[1680.0,1980.0]

=== LOG SUMMARY ===
{"entries":[{"error_logs":616,"error_pct":10.21,"service":"frontend-2","total_logs":6032},{"error_logs":569,"error_pct":9.78,"service":"frontend-1","total_logs":5819},{"error_logs":301,"error_pct":10.22,"service":"frontend-0","total_logs":2946},{"error_logs":6,"error_pct":0.11,"service":"adservice-0","total_logs":5639},{"error_logs":6,"error_pct":21.43,"service":"adservice-2","total_logs":28},{"error_logs":6,"error_pct":21.43,"service":"adservice-1","total_logs":28}],"mode":"errors","omitted_services":20,"service_count":26}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":84.6,"error_pct":0.0,"p95_during_ms":518.877,"p95_pre_ms":281.09139999999667,"service":"frontend","spans":51381},{"delta_pct":-19.1,"error_pct":0.0,"p95_during_ms":0.8734999999999998,"p95_pre_ms":1.07915,"service":"emailservice","spans":174},{"delta_pct":-8.3,"error_pct":0.0,"p95_during_ms":0.4199999999999991,"p95_pre_ms":0.45779999999999976,"service":"shippingservice","spans":1215},{"delta_pct":-1.5,"error_pct":0.0,"p95_during_ms":13.812249999999999,"p95_pre_ms":14.028299999999994,"service":"productcatalogservice","spans":23648},{"delta_pct":1.2,"error_pct":0.0,"p95_during_ms":2.2929,"p95_pre_ms":2.2650999999999994,"service":"redis","spans":4543},{"delta_pct":1.0,"error_pct":0.0,"p95_during_ms":4.9773499999999995,"p95_pre_ms":4.927899999999999,"service":"recommendationservice","spans":6280},{"delta_pct":0.5,"error_pct":0.0,"p95_during_ms":144.99874999999997,"p95_pre_ms":144.20775,"service":"checkoutservice","spans":2054},{"delta_pct":-0.2,"error_pct":0.0,"p95_during_ms":3.7964500000000005,"p95_pre_ms":3.8047999999999993,"service":"cartservice","spans":4196}],"omitted_services":0,"service_count":8}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=9 omitted_edges=0
[{"evidence_source":"metric","onset_rel_s":1020.0,"rank":1,"service":"frontend","severity_z":15.6},{"evidence_source":"metric","onset_rel_s":1020.0,"rank":2,"service":"hipstershop","severity_z":13.306},{"evidence_source":"metric","onset_rel_s":1020.0,"rank":3,"service":"node-2","severity_z":13.135},{"evidence_source":"metric","onset_rel_s":1140.0,"rank":4,"service":"node-3","severity_z":14.948},{"evidence_source":"metric","onset_rel_s":1260.0,"rank":5,"service":"k8s-master2","severity_z":146.199},{"evidence_source":"metric","onset_rel_s":1320.0,"rank":6,"service":"redis-cart","severity_z":15.6},{"evidence_source":"metric","onset_rel_s":1560.0,"rank":7,"service":"currencyservice","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1560.0,"rank":8,"service":"node-6","severity_z":26.3},{"evidence_source":"metric","onset_rel_s":1680.0,"rank":9,"service":"shippingservice","severity_z":30.556},{"evidence_source":"metric","onset_rel_s":1740.0,"rank":10,"service":"tidb-tikv","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1800.0,"rank":11,"service":"cartservice","severity_z":12.725},{"evidence_source":"metric","onset_rel_s":1860.0,"rank":12,"service":"example-ant","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1860.0,"rank":13,"service":"node-1","severity_z":10.493},{"evidence_source":"none","onset_rel_s":null,"rank":14,"service":"paymentservice","severity_z":0.0}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"cartservice","caller":"frontend"},{"callee":"shippingservice","caller":"frontend"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

{"confidence":"medium","reason":"Rank adservice first because adservice has direct log evidence; frontend is second despite propagation rank 1 because onset ordering alone does not establish the causal origin. The remaining entries preserve evidence-supported alternatives so the ranking retains calibrated uncertainty instead of collapsing to one answer.","services":["adservice","node-6","currencyservice-2","redis-cart-0","shippingservice-0"]}

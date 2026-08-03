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
opaque_id: INC-F206E4DA4597
observation_window={"duration_rel_s":1740.0,"source_metric_rows":30}
selection_summary={"candidate_count":60,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":477,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["adservice","adservice-0","adservice-1","adservice-2","cartservice","cartservice-0","cartservice-1","cartservice-2","checkoutservice","checkoutservice-0","checkoutservice-1","checkoutservice-2","currencyservice","currencyservice-0","currencyservice-1","currencyservice-2","emailservice","emailservice-0","emailservice-1","emailservice-2","example-ant-10-29152320-7q99m","example-ant-29152320-kszxj","frontend","frontend-0","frontend-1","frontend-2","hipstershop","k8s-master1","k8s-master2","k8s-master3","node-1","node-2","node-3","node-4","node-5","node-6","node-7","node-8","paymentservice","paymentservice-0","paymentservice-1","paymentservice-2","productcatalogservice","productcatalogservice-0","productcatalogservice-1","productcatalogservice-2","recommendationservice","recommendationservice-0","recommendationservice-1","recommendationservice-2","redis","redis-cart","redis-cart-0","shippingservice","shippingservice-0","shippingservice-1","shippingservice-2","tidb-pd","tidb-tidb","tidb-tikv"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[13.594,40.781,67.969,95.156,122.344,149.531,176.719,203.906,231.094,258.281,285.469,312.656,339.844,367.031,394.219,421.406,448.594,475.781,502.969,530.156,557.344,584.531,611.719,638.906,666.094,693.281,720.469,747.656,774.844,802.031,829.219,856.406,883.594,910.781,937.969,965.156,992.344,1019.531,1046.719,1073.906,1101.094,1128.281,1155.469,1182.656,1209.844,1237.031,1264.219,1291.406,1318.594,1345.781,1372.969,1400.156,1427.344,1454.531,1481.719,1508.906,1536.094,1563.281,1590.469,1617.656,1644.844,1672.031,1699.219,1726.406]
[M1] rank=1 service=adservice-1 metric=pod_memory_working_set_bytes baseline=7.796667 peak=22423770.44 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,116.95,-116.95,0,0,0,0,0,0,18643484.11,-18642668.72,-815.39,0,0,0,0,0,0,0,0,0,0,22423770.44,-22423770.44
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M2] rank=2 service=adservice-2 metric=pod_memory_working_set_bytes baseline=389.738667 peak=8287284.13 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,5759.13,-5759.13,0,0,0,0,0,0,0,86.95,-86.95,0,0,0,0,0,0,8237175.88,-8237175.88,0,0,7288852.7,-7288852.7,5271.13,-5271.13,0,8287284.13,-8287284.13,0
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M3] rank=3 service=node-7 metric=node_network_receive_bytes_total baseline=164.07 peak=164.04 signed_z=-999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:164.07,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,-0.03
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M4] rank=4 service=paymentservice-0 metric=pod_memory_working_set_bytes baseline=1244.343333 peak=620384.66 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:1151.42,-421.07,-513.84,1033.62,-939.14,1132.27,-367.58,-140.19,50.87,603.51,136.48,-192.27,381.95,-162.87,292.31,-1815.11,1594.31,260.94,618299.05,-618103.85,-962.13,1077.44,-1310.78,564.21,-464.28,722.15,-547.59,569.23,-128.13,1240.06
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M5] rank=5 service=tidb-tidb metric=qps baseline=0.0 peak=0.31 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.31,-0.07,-0.24,0,0,0,0,0,0,0,0,0,0.18,-0.18,0
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M6] rank=6 service=tidb-tikv metric=write_wal_mbps baseline=13.224667 peak=1736.31 signed_z=200.943 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:10.44,1.05,-9.4,-1.05,19.85,-9.4,1.04,12.23,7.13,-19.36,-2.09,-8.35,22.67,-13.27,-1.05,518.23,1207.64,-1709.47,6.09,-31.89,10.45,-1.05,-7.31,8.36,-1.05,1.05,-1.05,320.09,-183.31,-114.29
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M7] rank=7 service=tidb-tikv metric=read_mbps baseline=22331.585333 peak=637893.8 signed_z=184.449 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:21421.67,-1126.58,306.47,-309.87,2391.33,-1925.29,726.49,8180.11,-8481.44,464.13,-1203.6,1350.38,9803.78,-11169.38,253.36,446841.86,170370.38,-606223.04,-11025.74,926.62,-1167.97,705.26,-927.66,355.4,-461.54,1736.65,-1089.78,234178.71,-231841,-1112.09
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M8] rank=8 service=paymentservice-1 metric=rrt_max baseline=2543.133333 peak=50857.0 signed_z=59.635 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:2049,-71,2204,-2284,387,53,-376,1387,-1746,1001,-105,-815,2620,-1209,-778,585,-187,-801,-138,237,-105,-247,2767,-2066,-272,48767,-47618,-1572,76,31
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M9] rank=9 service=currencyservice-0 metric=rrt_max baseline=5933.933333 peak=105717.0 signed_z=48.269 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:3953,611,-920,5593,988,-5001,-427,2541,-1630,3500,-5938,1806,331,963,-1382,4412,990,1581,32312,-35453,-1343,-3438,2593,-383,99458,-94550,-6119,862,1950,-808
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M10] rank=10 service=paymentservice metric=rrt_max baseline=3246.6 peak=50857.0 signed_z=39.998 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:2290,-209,2676,-627,-1845,53,156,1614,-1292,-212,1626,-2418,2492,1682,-3522,438,-187,812,-329,-1090,64,1409,955,-1054,194,47181,-46840,-899,-483,-734
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M11] rank=11 service=currencyservice metric=rrt_max baseline=9031.8 peak=105717.0 signed_z=39.683 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:8001,-659,1226,669,988,-760,6002,-7754,2425,-930,3505,-6676,-630,3267,-1392,36327,-33219,1581,32312,-22662,-14134,618,434,95599,1579,-94550,-3478,23050,-22879,-808
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M12] rank=12 service=currencyservice-1 metric=rrt_max baseline=8085.133333 peak=104138.0 signed_z=34.126 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:8001,-659,1226,-1111,867,1141,6002,-7754,-2351,-475,7826,-6676,-2052,4689,-1392,36327,-38565,1167,4356,11054,-18091,4575,434,95599,-96384,1773,-1838,23050,-27067,3366
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[1620.0,1740.0]

=== LOG SUMMARY ===
{"entries":[{"error_logs":6,"error_pct":1.8,"service":"adservice-1","total_logs":334}],"mode":"errors","omitted_services":22,"service_count":23}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":-10.8,"error_pct":0.0,"p95_during_ms":0.9535,"p95_pre_ms":1.0685,"service":"emailservice","spans":487},{"delta_pct":-6.3,"error_pct":0.0,"p95_during_ms":4.141199999999991,"p95_pre_ms":4.418399999999997,"service":"cartservice","spans":11756},{"delta_pct":6.2,"error_pct":0.0,"p95_during_ms":0.5224,"p95_pre_ms":0.492,"service":"shippingservice","spans":3414},{"delta_pct":5.0,"error_pct":0.0,"p95_during_ms":136.12079999999997,"p95_pre_ms":129.6155,"service":"checkoutservice","spans":5728},{"delta_pct":-3.1,"error_pct":0.0,"p95_during_ms":4.8623,"p95_pre_ms":5.015449999999999,"service":"recommendationservice","spans":17640},{"delta_pct":2.2,"error_pct":0.0,"p95_during_ms":3.08035,"p95_pre_ms":3.014199999999999,"service":"redis","spans":12735},{"delta_pct":-1.2,"error_pct":0.0,"p95_during_ms":14.117999999999993,"p95_pre_ms":14.289599999999998,"service":"productcatalogservice","spans":66342},{"delta_pct":0.5,"error_pct":0.0,"p95_during_ms":88.12839999999996,"p95_pre_ms":87.72229999999999,"service":"frontend","spans":143565}],"omitted_services":0,"service_count":8}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=6 omitted_edges=0
[{"evidence_source":"metric","onset_rel_s":900.0,"rank":1,"service":"tidb-tidb","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":960.0,"rank":2,"service":"tidb-tikv","severity_z":200.943},{"evidence_source":"metric","onset_rel_s":960.0,"rank":3,"service":"shippingservice","severity_z":13.421},{"evidence_source":"metric","onset_rel_s":1080.0,"rank":4,"service":"paymentservice","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1440.0,"rank":5,"service":"currencyservice","severity_z":48.269},{"evidence_source":"metric","onset_rel_s":1680.0,"rank":6,"service":"adservice","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1740.0,"rank":7,"service":"node-7","severity_z":999.0},{"evidence_source":"none","onset_rel_s":null,"rank":8,"service":"recommendationservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":9,"service":"checkoutservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":10,"service":"hipstershop","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":11,"service":"productcatalogservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":12,"service":"tidb-pd","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":13,"service":"redis-cart","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":14,"service":"frontend","severity_z":0.0}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"productcatalogservice","caller":"checkoutservice"},{"callee":"shippingservice","caller":"checkoutservice"},{"callee":"checkoutservice","caller":"frontend"},{"callee":"productcatalogservice","caller":"frontend"},{"callee":"recommendationservice","caller":"frontend"},{"callee":"shippingservice","caller":"frontend"},{"callee":"productcatalogservice","caller":"recommendationservice"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

{"confidence":"medium","reason":"Rank adservice-1 first because adservice-1 has direct pod_memory_working_set_bytes evidence (signed-z 999, persistence 0 bins); tidb-tidb is second despite propagation rank 1 because onset ordering alone does not establish the causal origin.","services":["adservice-1","tidb-tidb"]}

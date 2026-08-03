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
opaque_id: INC-719F153ECB78
observation_window={"duration_rel_s":1740.0,"source_metric_rows":30}
selection_summary={"candidate_count":60,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":476,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["adservice","adservice-0","adservice-1","adservice-2","cartservice","cartservice-0","cartservice-1","cartservice-2","checkoutservice","checkoutservice-0","checkoutservice-1","checkoutservice-2","currencyservice","currencyservice-0","currencyservice-1","currencyservice-2","emailservice","emailservice-0","emailservice-1","emailservice-2","example-ant-10-29155200-sh4b9","example-ant-29155200-tblqb","frontend","frontend-0","frontend-1","frontend-2","hipstershop","k8s-master1","k8s-master2","k8s-master3","node-1","node-2","node-3","node-4","node-5","node-6","node-7","node-8","paymentservice","paymentservice-0","paymentservice-1","paymentservice-2","productcatalogservice","productcatalogservice-0","productcatalogservice-1","productcatalogservice-2","recommendationservice","recommendationservice-0","recommendationservice-1","recommendationservice-2","redis","redis-cart","redis-cart-0","shippingservice","shippingservice-0","shippingservice-1","shippingservice-2","tidb-pd","tidb-tidb","tidb-tikv"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[13.594,40.781,67.969,95.156,122.344,149.531,176.719,203.906,231.094,258.281,285.469,312.656,339.844,367.031,394.219,421.406,448.594,475.781,502.969,530.156,557.344,584.531,611.719,638.906,666.094,693.281,720.469,747.656,774.844,802.031,829.219,856.406,883.594,910.781,937.969,965.156,992.344,1019.531,1046.719,1073.906,1101.094,1128.281,1155.469,1182.656,1209.844,1237.031,1264.219,1291.406,1318.594,1345.781,1372.969,1400.156,1427.344,1454.531,1481.719,1508.906,1536.094,1563.281,1590.469,1617.656,1644.844,1672.031,1699.219,1726.406]
[M1] rank=1 service=adservice-1 metric=pod_fs_reads_bytes baseline=0.0 peak=1132.35 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1132.35,-1132.35,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M2] rank=2 service=node-2 metric=node_filesystem_usage_rate baseline=29.795 peak=29.8 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:29.795,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.005,0,0,0,0,-0.005
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M3] rank=3 service=redis-cart-0 metric=pod_processes baseline=1.0 peak=2.0 signed_z=500.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,-1,0,0,0,0,0,0,0,0,0
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M4] rank=4 service=tidb-tidb metric=connection_count baseline=2.0 peak=3.0 signed_z=333.333 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:2,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,-1,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M5] rank=5 service=emailservice-1 metric=rrt_max baseline=3277.266667 peak=66063.0 signed_z=85.722 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:3483,514,-1336,809,-1037,1305,1145,-1764,-296,141,1687,-1779,-490,504,-89,234,785,62247,-60031,-3458,-101,105,870,-747,153,824,-1698,1172,-108,-54
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M6] rank=6 service=cartservice-0 metric=rrt baseline=1680.211333 peak=15353.77 signed_z=67.667 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:2234.71,-681.24,-4.61,201.07,-101.57,-71.47,-47.89,299.53,-329.96,460.93,-390.05,-74.53,86.83,275.41,-285.09,238.65,-414.02,180.86,13776.21,-13649.25,-296.77,604.17,-356.39,-181.18,524.65,-521.62,-221.26,184.7,532.76,-438.91
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M7] rank=7 service=emailservice metric=rrt_max baseline=4060.266667 peak=66063.0 signed_z=53.373 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:3553,690,-1582,1073,-96,100,1145,-1519,-516,116,1687,-1779,4066,-1312,-435,-1363,-12,62247,-60031,-1564,-1337,2010,-1057,-906,2570,3982,-5314,-214,1854,-1737
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M8] rank=8 service=cartservice-0 metric=rrt_max baseline=3908.4 peak=78637.0 signed_z=53.219 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:7456,-4907,-161,1492,344,-467,-823,1112,-1435,1267,654,-1534,-337,3938,-2486,-597,-1083,1668,74536,-74861,-1478,3539,-1050,-1789,2390,-2388,-1052,584,2556,-2236
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M9] rank=9 service=emailservice-1 metric=rrt baseline=1686.584667 peak=6697.42 signed_z=30.327 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:1777.17,-74.92,158.42,-151.92,-235.33,399.25,-371.34,159.67,197.09,-445.42,475.71,-301.83,-121.38,439.12,-277.93,53.81,642.66,4374.59,-4274.25,-764,-64.5,-106.59,841.92,-775.75,-153.34,276.01,-442.92,407.5,147.17,-284.34
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M10] rank=10 service=cartservice-1 metric=rrt_max baseline=8677.4 peak=79237.0 signed_z=23.56 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:12063,-2506,277,-2580,-522,6952,-8024,1279,6342,-8996,1659,-826,5985,546,-4591,-2928,3292,-1446,73261,-73965,1264,-374,2567,-23,-3799,60994,-58092,6381,-7172,4244
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M11] rank=11 service=currencyservice-2 metric=rrt_max baseline=1859.0 peak=8194.0 signed_z=13.329 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:1339,151,37,1132,-970,-89,182,1348,-1613,742,-450,27,276,-565,42,35,1529,-1730,211,-34,-367,178,184,428,-279,26,1742,-1449,6131,-6712
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M12] rank=12 service=emailservice metric=rrt baseline=1750.869333 peak=3811.13 signed_z=11.918 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:1749.67,29.54,-302.21,364.53,-228.91,327.05,-464.09,230.2,76.5,-257.61,316.17,-156.81,91.14,293.99,-63.33,-225.34,59.18,1971.46,-1721.16,-77.33,-319.1,209.79,82.25,-205.8,44.98,348.49,-166.33,-108.2,372.11,-490.45
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[1380.0,1740.0]

=== LOG SUMMARY ===
{"entries":[{"change_pct":-76.2,"n_during":10,"n_pre":42,"service":"emailservice-1"},{"change_pct":-76.2,"n_during":10,"n_pre":42,"service":"emailservice-2"},{"change_pct":-76.2,"n_during":20,"n_pre":84,"service":"paymentservice-1"},{"change_pct":-76.2,"n_during":20,"n_pre":84,"service":"paymentservice-2"},{"change_pct":-75.0,"n_during":93,"n_pre":372,"service":"checkoutservice-2"},{"change_pct":-75.0,"n_during":3012,"n_pre":12071,"service":"currencyservice-1"},{"change_pct":-75.0,"n_during":704,"n_pre":2821,"service":"frontend-0"},{"change_pct":-74.9,"n_during":168,"n_pre":668,"service":"recommendationservice-0"}],"mode":"volume","omitted_services":15,"service_count":23}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":16.5,"error_pct":0.0,"p95_during_ms":5.559800000000005,"p95_pre_ms":4.773499999999999,"service":"cartservice","spans":3585},{"delta_pct":-11.8,"error_pct":0.0,"p95_during_ms":0.9670000000000001,"p95_pre_ms":1.0966499999999997,"service":"emailservice","spans":151},{"delta_pct":8.2,"error_pct":0.0,"p95_during_ms":156.69329999999997,"p95_pre_ms":144.8213,"service":"checkoutservice","spans":1774},{"delta_pct":3.0,"error_pct":0.0,"p95_during_ms":3.4945,"p95_pre_ms":3.39205,"service":"redis","spans":3885},{"delta_pct":-1.7,"error_pct":0.0,"p95_during_ms":92.18819999999995,"p95_pre_ms":93.753,"service":"frontend","spans":43778},{"delta_pct":1.7,"error_pct":0.0,"p95_during_ms":5.3614999999999995,"p95_pre_ms":5.269949999999999,"service":"recommendationservice","spans":5368},{"delta_pct":-1.6,"error_pct":0.0,"p95_during_ms":14.311749999999998,"p95_pre_ms":14.54145,"service":"productcatalogservice","spans":20202},{"delta_pct":0.9,"error_pct":0.0,"p95_during_ms":0.4973499999999995,"p95_pre_ms":0.493,"service":"shippingservice","spans":1061}],"omitted_services":0,"service_count":8}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=6 omitted_edges=0
[{"evidence_source":"metric","onset_rel_s":900.0,"rank":1,"service":"adservice","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1020.0,"rank":2,"service":"tidb-tidb","severity_z":333.333},{"evidence_source":"metric","onset_rel_s":1020.0,"rank":3,"service":"emailservice","severity_z":85.722},{"evidence_source":"metric","onset_rel_s":1080.0,"rank":4,"service":"cartservice","severity_z":67.667},{"evidence_source":"metric","onset_rel_s":1140.0,"rank":5,"service":"redis-cart","severity_z":500.0},{"evidence_source":"metric","onset_rel_s":1440.0,"rank":6,"service":"node-2","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1680.0,"rank":7,"service":"currencyservice","severity_z":13.329},{"evidence_source":"none","onset_rel_s":null,"rank":8,"service":"recommendationservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":9,"service":"shippingservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":10,"service":"tidb-pd","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":11,"service":"productcatalogservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":12,"service":"k8s-master3","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":13,"service":"tidb-tikv","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":14,"service":"paymentservice","severity_z":0.0}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"productcatalogservice","caller":"recommendationservice"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

[excluded before optimizer]

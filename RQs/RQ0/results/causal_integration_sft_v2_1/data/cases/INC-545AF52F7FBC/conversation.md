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
opaque_id: INC-545AF52F7FBC
observation_window={"duration_rel_s":1740.0,"source_metric_rows":30}
selection_summary={"candidate_count":60,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":479,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["adservice","adservice-0","adservice-1","adservice-2","cartservice","cartservice-0","cartservice-1","cartservice-2","checkoutservice","checkoutservice-0","checkoutservice-1","checkoutservice-2","currencyservice","currencyservice-0","currencyservice-1","currencyservice-2","emailservice","emailservice-0","emailservice-1","emailservice-2","example-ant-10-29155200-sh4b9","example-ant-29155200-tblqb","frontend","frontend-0","frontend-1","frontend-2","hipstershop","k8s-master1","k8s-master2","k8s-master3","node-1","node-2","node-3","node-4","node-5","node-6","node-7","node-8","paymentservice","paymentservice-0","paymentservice-1","paymentservice-2","productcatalogservice","productcatalogservice-0","productcatalogservice-1","productcatalogservice-2","recommendationservice","recommendationservice-0","recommendationservice-1","recommendationservice-2","redis","redis-cart","redis-cart-0","shippingservice","shippingservice-0","shippingservice-1","shippingservice-2","tidb-pd","tidb-tidb","tidb-tikv"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[13.594,40.781,67.969,95.156,122.344,149.531,176.719,203.906,231.094,258.281,285.469,312.656,339.844,367.031,394.219,421.406,448.594,475.781,502.969,530.156,557.344,584.531,611.719,638.906,666.094,693.281,720.469,747.656,774.844,802.031,829.219,856.406,883.594,910.781,937.969,965.156,992.344,1019.531,1046.719,1073.906,1101.094,1128.281,1155.469,1182.656,1209.844,1237.031,1264.219,1291.406,1318.594,1345.781,1372.969,1400.156,1427.344,1454.531,1481.719,1508.906,1536.094,1563.281,1590.469,1617.656,1644.844,1672.031,1699.219,1726.406]
[M1] rank=1 service=k8s-master2 metric=node_filesystem_free_bytes baseline=9630775432.533333 peak=9638907904.0 signed_z=53.034 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:9630490624,-16384,401408,-57344,12288,-20480,20480,69632,-147456,0,0,0,352256,-233472,-258048,20480,-20480,8294400,-8404992,0,0,0,0,180224,-16384,-20480,20480,-266240,16384,-229376
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M2] rank=2 service=shippingservice-0 metric=rrt baseline=1073.319333 peak=3926.79 signed_z=45.999 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:1050,4.75,40.5,-10.27,-26.77,88.07,-167.7,-1.39,76.72,99.32,55.04,-195.84,41.99,70.98,-78.51,75.36,-43.06,-48.44,32.31,39.79,22.71,-0.09,-14.55,147.58,-250.57,2918.86,-2929.89,29.28,79.57,-36.97
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M3] rank=3 service=shippingservice-0 metric=rrt_max baseline=2482.666667 peak=42223.0 signed_z=31.909 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:1933,-95,32,1989,-1163,-607,49,-721,274,166,4767,-4891,558,193,236,1288,-1869,-321,-52,996,918,-1338,1474,2345,-4280,40342,-39041,-1111,611,-1023
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M4] rank=4 service=node-5 metric=node_memory_MemAvailable_bytes baseline=10431643101.866667 peak=9087582208.0 signed_z=-31.793 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:10494767104,-13406208,10039296,-105713664,2650112,62595072,9310208,6819840,-103264256,6856704,53694464,12349440,14397440,-41730048,-10465280,-33759232,-36511744,-232144896,-79056896,-208576512,-49250304,-431087616,80097280,-52965376,48844800,-29294592,-287612928,99987456,-34803712,16211968
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M5] rank=5 service=node-5 metric=node_memory_usage_rate baseline=34.696667 peak=42.75 signed_z=31.605 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:34.31,0.08,-0.06,0.63,-0.01,-0.37,-0.06,-0.04,0.61,-0.04,-0.32,-0.07,-0.05,0.25,0.07,0.2,0.22,1.38,0.48,1.24,0.29,2.58,-0.48,0.31,-0.29,0.18,1.71,-0.59,0.21,-0.1
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M6] rank=6 service=node-3 metric=node_memory_usage_rate baseline=46.076667 peak=26.36 signed_z=-23.176 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:44.96,0.14,0.07,0.22,0.07,0.02,0.12,0.68,0.08,0.35,-0.67,0.14,1.31,-0.1,0.15,-1.76,0.04,-19.46,0.85,-0.13,0.28,0,0.57,0.07,0.07,0.04,0.19,0.3,0.31,0.03
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M7] rank=7 service=node-3 metric=node_memory_MemAvailable_bytes baseline=8508260625.066667 peak=11814744064.0 signed_z=23.165 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:8695328768,-22589440,-13049856,-36294656,-10657792,-4710400,-19648512,-114814976,-12828672,-59109376,113459200,-24637440,-219435008,16924672,-24723456,294789120,-5550080,3262291968,-142303232,21737472,-47001600,360448,-95473664,-12599296,-11399168,-7475200,-30306304,-51851264,-50831360,-5640192
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M8] rank=8 service=shippingservice metric=rrt_max baseline=5878.0 peak=42223.0 signed_z=22.025 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:4600,13,437,865,4633,-5869,-612,1997,-943,-227,1730,1234,-1535,1024,-2880,2240,-1219,1438,-1350,1933,-1307,-1007,-1379,5530,3560,29317,-36407,4795,-5954,1814
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M9] rank=9 service=node-2 metric=node_disk_written_bytes_total baseline=1351.678667 peak=6451.2 signed_z=14.843 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:1092.27,273.06,0,0,273.07,0,-1092.27,819.2,0,307.2,-307.2,580.27,-853.33,546.13,-819.2,819.2,-307.2,1877.33,2491.74,750.93,-1843.2,-3037.87,0.21,272.86,443.73,750.94,2013.86,-2662.4,-34.13,-443.73
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M10] rank=10 service=adservice-0 metric=pod_cpu_usage baseline=0.01 peak=0.13 signed_z=13.772 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.01,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.01,0,0,0,0,0,0,0,0,0,0,0,0,0.11,-0.12
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M11] rank=11 service=currencyservice-2 metric=rrt_max baseline=3575.866667 peak=25482.0 signed_z=8.162 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:11425,-9694,1411,-1127,1066,-1485,2696,-2499,506,6045,-3844,-2203,-611,457,1151,-1726,23914,-23532,-343,911,-793,1446,-1191,1494,1237,-2225,1597,-2324,749,1926
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M12] rank=12 service=shippingservice-2 metric=rrt_max baseline=2845.6 peak=12906.0 signed_z=8.083 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:1500,1276,-820,3959,-3594,1717,-987,-1588,257,879,-511,654,1527,170,-2632,964,-775,388,269,119,-937,-238,1348,-628,10589,-10285,-284,-887,3207,-3285
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[960.0,1080.0]

=== LOG SUMMARY ===
{"entries":[{"error_logs":12273,"error_pct":14.65,"service":"adservice-0","total_logs":83752},{"error_logs":1099,"error_pct":7.98,"service":"frontend-2","total_logs":13770},{"error_logs":1000,"error_pct":7.86,"service":"frontend-0","total_logs":12724},{"error_logs":1000,"error_pct":7.93,"service":"frontend-1","total_logs":12607},{"error_logs":9,"error_pct":28.12,"service":"adservice-1","total_logs":32},{"error_logs":9,"error_pct":28.12,"service":"adservice-2","total_logs":32}],"mode":"errors","omitted_services":18,"service_count":24}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":-16.9,"error_pct":0.0,"p95_during_ms":3.7117999999999998,"p95_pre_ms":4.4684,"service":"redis","spans":12086},{"delta_pct":-15.2,"error_pct":0.0,"p95_during_ms":5.2675,"p95_pre_ms":6.208949999999995,"service":"cartservice","spans":11184},{"delta_pct":-9.5,"error_pct":0.0,"p95_during_ms":5.7301,"p95_pre_ms":6.3325,"service":"recommendationservice","spans":16726},{"delta_pct":-9.2,"error_pct":0.0,"p95_during_ms":0.9803,"p95_pre_ms":1.0790999999999997,"service":"emailservice","spans":464},{"delta_pct":-2.5,"error_pct":0.0,"p95_during_ms":125.30725,"p95_pre_ms":128.49365,"service":"checkoutservice","spans":5466},{"delta_pct":2.1,"error_pct":0.0,"p95_during_ms":14.401199999999996,"p95_pre_ms":14.101,"service":"productcatalogservice","spans":63075},{"delta_pct":1.7,"error_pct":5.17,"p95_during_ms":89.24719999999985,"p95_pre_ms":87.72775,"service":"frontend","spans":136596},{"delta_pct":-0.3,"error_pct":0.0,"p95_during_ms":0.5190999999999996,"p95_pre_ms":0.5207999999999997,"service":"shippingservice","spans":3248}],"omitted_services":0,"service_count":8}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=8 omitted_edges=0
[{"evidence_source":"metric","onset_rel_s":1020.0,"rank":1,"service":"k8s-master2","severity_z":53.034},{"evidence_source":"metric","onset_rel_s":1020.0,"rank":2,"service":"node-3","severity_z":23.176},{"evidence_source":"metric","onset_rel_s":1080.0,"rank":3,"service":"node-2","severity_z":14.843},{"evidence_source":"metric","onset_rel_s":1200.0,"rank":4,"service":"node-5","severity_z":31.793},{"evidence_source":"metric","onset_rel_s":1500.0,"rank":5,"service":"shippingservice","severity_z":45.999},{"evidence_source":"metric","onset_rel_s":1680.0,"rank":6,"service":"adservice","severity_z":13.772},{"evidence_source":"none","onset_rel_s":null,"rank":7,"service":"currencyservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":8,"service":"checkoutservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":9,"service":"hipstershop","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":10,"service":"cartservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":11,"service":"k8s-master1","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":12,"service":"emailservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":13,"service":"tidb-tidb","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":14,"service":"tidb-tikv","severity_z":0.0}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"cartservice","caller":"checkoutservice"},{"callee":"emailservice","caller":"checkoutservice"},{"callee":"shippingservice","caller":"checkoutservice"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

{"confidence":"medium","reason":"Rank adservice first because adservice has direct pod_cpu_usage evidence (signed-z 13.77, persistence 0 bins); k8s-master2 is second despite propagation rank 1 because onset ordering alone does not establish the causal origin. The remaining entries preserve evidence-supported alternatives so the ranking retains calibrated uncertainty instead of collapsing to one answer.","services":["adservice","k8s-master2","node-3","node-5","node-2"]}

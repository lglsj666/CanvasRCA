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
opaque_id: INC-CE440D6EB495
observation_window={"duration_rel_s":1740.0,"source_metric_rows":30}
selection_summary={"candidate_count":60,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":499,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["adservice","adservice-0","adservice-1","adservice-2","cartservice","cartservice-0","cartservice-1","cartservice-2","checkoutservice","checkoutservice-0","checkoutservice-1","checkoutservice-2","currencyservice","currencyservice-0","currencyservice-1","currencyservice-2","emailservice","emailservice-0","emailservice-1","emailservice-2","example-ant-10-29163840-4fv9c","example-ant-29163840-4gqcw","frontend","frontend-0","frontend-1","frontend-2","hipstershop","k8s-master1","k8s-master2","k8s-master3","node-1","node-2","node-3","node-4","node-5","node-6","node-7","node-8","paymentservice","paymentservice-0","paymentservice-1","paymentservice-2","productcatalogservice","productcatalogservice-0","productcatalogservice-1","productcatalogservice-2","recommendationservice","recommendationservice-0","recommendationservice-1","recommendationservice-2","redis","redis-cart","redis-cart-0","shippingservice","shippingservice-0","shippingservice-1","shippingservice-2","tidb-pd","tidb-tidb","tidb-tikv"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[13.594,40.781,67.969,95.156,122.344,149.531,176.719,203.906,231.094,258.281,285.469,312.656,339.844,367.031,394.219,421.406,448.594,475.781,502.969,530.156,557.344,584.531,611.719,638.906,666.094,693.281,720.469,747.656,774.844,802.031,829.219,856.406,883.594,910.781,937.969,965.156,992.344,1019.531,1046.719,1073.906,1101.094,1128.281,1155.469,1182.656,1209.844,1237.031,1264.219,1291.406,1318.594,1345.781,1372.969,1400.156,1427.344,1454.531,1481.719,1508.906,1536.094,1563.281,1590.469,1617.656,1644.844,1672.031,1699.219,1726.406]
[M1] rank=1 service=node-4 metric=node_disk_read_bytes_total baseline=0.0 peak=10922.67 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,10922.67,-10922.67,0,0,0,0,0,0,0
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M2] rank=2 service=paymentservice-1 metric=pod_memory_working_set_bytes baseline=560.818667 peak=471871.21 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:262.08,284.11,15.5,-231.04,758.62,-1089.27,398.68,149.96,928.79,-1308.54,358.13,142.92,14.96,5.77,-234.44,-456.23,0,585.42,-585.42,1099.55,-673.84,399.41,-825.12,1186.43,470684.78,-471871.21,0,0,0,0
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M3] rank=3 service=tidb-tidb metric=qps baseline=0.0 peak=0.23 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.23,-0.23,0,0,0,0,0,0,0,0,0.135,-0.135,0,0,0
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M4] rank=4 service=currencyservice-0 metric=pod_memory_working_set_bytes baseline=2727.529333 peak=1947618.03 signed_z=798.608 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:804.7,341.06,995.1,-1140.66,2345.09,8088.89,-8873.62,-1247.65,1576.65,-597.75,524.07,-831.9,599.37,-107.24,-348.32,465.26,-1346.42,1946371.4,-1947618.03,214.01,63.8,48.1,-18.49,48.38,244.3,268,-136.17,1405.42,-741.54,1099410.93
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M5] rank=5 service=tidb-tikv metric=write_wal_mbps baseline=15.849333 peak=589.02 signed_z=73.583 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:27.89,-16.4,-1.05,2.09,-2.09,16.4,-16.4,21.45,-20.4,0,16.4,-16.4,0,0,-1.05,578.58,-573.35,-5.23,21.45,-20.4,14.31,-15.36,1.05,-1.05,-9.4,340.89,-338.95,8.51,20.4,-20.4
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M6] rank=6 service=tidb-tikv metric=read_mbps baseline=16274.100667 peak=326571.96 signed_z=72.232 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:24284.33,-9976.95,-32.58,-1702.56,400.29,11685.11,-10072.93,-458.87,-146.53,1761.78,9549.02,-10612.73,-183.25,-733.02,627.8,312183.05,-311291.2,-348.69,-1048.54,1724.14,9766.97,-11562.62,984.82,14.4,187.12,107350.08,-107957.35,27.04,1245.18,-1074.69
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M7] rank=7 service=k8s-master2 metric=node_disk_write_time_seconds_total baseline=0.028 peak=1.0 signed_z=27.427 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.02,0,0,-0.01,0.01,-0.01,0.01,0,0,0,0,0,0.14,-0.14,0,0,0,0.98,-0.98,0,0,0,0.21,-0.22,0.01,0,0.78,-0.79,0.01,-0.01
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M8] rank=8 service=k8s-master3 metric=node_filesystem_free_bytes baseline=8183439633.066667 peak=8200171520.0 signed_z=22.273 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:8183861248,0,-118784,45056,-65536,20480,0,0,114688,-221184,0,-40960,0,-2076672,36864,0,0,-151552,0,2072576,32768,0,0,0,-32768,16695296,-16732160,98304,0,0
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M9] rank=9 service=k8s-master3 metric=node_filesystem_usage_rate baseline=68.391333 peak=68.33 signed_z=-18.043 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:68.39,0,0,0,0,0,0,0,0,0,0,0,0,0.01,0,0,0,0,0,-0.01,0,0,0,0,0,-0.06,0.06,0,0,0
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M10] rank=10 service=cartservice-2 metric=rrt baseline=1645.026 peak=5933.29 signed_z=14.404 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:2187.42,-591.42,11.86,-219.43,35.46,64.67,-43.14,18.32,329.34,-290.22,15.16,-58.73,71.86,945.8,-684.23,-255.47,130.14,-269.37,125.83,-64.78,4474.22,-4278.03,-204.66,157,-120.25,115.49,2584.1,-2675.59,105.41,-47.62
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M11] rank=11 service=shippingservice-1 metric=rrt baseline=1086.292 peak=2442.38 signed_z=13.159 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:962.69,287.87,-44.05,-116.19,-14.02,-25.88,-10.65,-71.37,30.15,68.68,-78.04,120.57,-109.66,168.1,148.18,-243.88,-29.8,1399.68,-1460.66,94.89,55.17,232.9,-98.68,-211.91,-33.55,-18.26,76.74,72.91,-16.32,-148.71
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M12] rank=12 service=emailservice-2 metric=rrt baseline=1694.788 peak=4006.67 signed_z=11.741 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:2020.5,-257.33,-159.09,85.5,90.09,64,2.83,-160.67,-129.5,153,-62.9,-203.79,-25.81,643.31,-703.02,2649.55,-2393.67,-109.67,273.81,-505.31,432,-30,-210.33,181.67,364.66,-150.33,322.36,-292.86,-34.06,0
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[1200.0,1320.0]

=== LOG SUMMARY ===
{"entries":[{"error_logs":2,"error_pct":0.64,"service":"currencyservice-2","total_logs":313}],"mode":"errors","omitted_services":22,"service_count":23}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":34.1,"error_pct":0.0,"p95_during_ms":5.428299999999998,"p95_pre_ms":4.048199999999999,"service":"cartservice","spans":3519},{"delta_pct":15.3,"error_pct":0.0,"p95_during_ms":0.5513999999999994,"p95_pre_ms":0.4780499999999997,"service":"shippingservice","spans":1021},{"delta_pct":-11.1,"error_pct":0.0,"p95_during_ms":0.9168,"p95_pre_ms":1.0312,"service":"emailservice","spans":146},{"delta_pct":-7.6,"error_pct":0.0,"p95_during_ms":128.8253499999998,"p95_pre_ms":139.40579999999977,"service":"checkoutservice","spans":1730},{"delta_pct":6.2,"error_pct":0.0,"p95_during_ms":2.730199999999998,"p95_pre_ms":2.5700000000000003,"service":"redis","spans":3810},{"delta_pct":-3.2,"error_pct":0.0,"p95_during_ms":13.453649999999996,"p95_pre_ms":13.904599999999999,"service":"productcatalogservice","spans":19853},{"delta_pct":-2.4,"error_pct":0.0,"p95_during_ms":4.96,"p95_pre_ms":5.081,"service":"recommendationservice","spans":5274},{"delta_pct":0.6,"error_pct":0.0,"p95_during_ms":89.18949999999992,"p95_pre_ms":88.69959999999999,"service":"frontend","spans":43067}],"omitted_services":0,"service_count":8}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=7 omitted_edges=1
[{"evidence_source":"metric","onset_rel_s":900.0,"rank":1,"service":"tidb-tidb","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":900.0,"rank":2,"service":"tidb-tikv","severity_z":73.583},{"evidence_source":"metric","onset_rel_s":900.0,"rank":3,"service":"emailservice","severity_z":11.741},{"evidence_source":"metric","onset_rel_s":1020.0,"rank":4,"service":"currencyservice","severity_z":798.608},{"evidence_source":"metric","onset_rel_s":1020.0,"rank":5,"service":"k8s-master2","severity_z":27.427},{"evidence_source":"metric","onset_rel_s":1020.0,"rank":6,"service":"shippingservice","severity_z":13.159},{"evidence_source":"trace","onset_rel_s":1214.4,"rank":7,"service":"cartservice","severity_z":7.402},{"evidence_source":"trace","onset_rel_s":1214.4,"rank":8,"service":"redis","severity_z":8.197},{"evidence_source":"metric","onset_rel_s":1260.0,"rank":9,"service":"node-4","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1440.0,"rank":10,"service":"paymentservice","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1500.0,"rank":11,"service":"k8s-master3","severity_z":22.273},{"evidence_source":"none","onset_rel_s":null,"rank":12,"service":"adservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":13,"service":"productcatalogservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":14,"service":"frontend","severity_z":0.0}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"redis","caller":"cartservice"},{"callee":"cartservice","caller":"frontend"},{"callee":"productcatalogservice","caller":"frontend"},{"callee":"shippingservice","caller":"frontend"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

{"confidence":"medium","reason":"Rank currencyservice-2 first because currencyservice-2 has direct log evidence; tidb-tidb is second despite propagation rank 1 because onset ordering alone does not establish the causal origin.","services":["currencyservice-2","tidb-tidb"]}

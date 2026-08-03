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
opaque_id: INC-34A7B23CE0BE
observation_window={"duration_rel_s":1740.0,"source_metric_rows":30}
selection_summary={"candidate_count":60,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":483,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["adservice","adservice-0","adservice-1","adservice-2","cartservice","cartservice-0","cartservice-1","cartservice-2","checkoutservice","checkoutservice-0","checkoutservice-1","checkoutservice-2","currencyservice","currencyservice-0","currencyservice-1","currencyservice-2","emailservice","emailservice-0","emailservice-1","emailservice-2","example-ant-10-29172480-4qwqp","example-ant-29172480-8w684","frontend","frontend-0","frontend-1","frontend-2","hipstershop","k8s-master1","k8s-master2","k8s-master3","node-1","node-2","node-3","node-4","node-5","node-6","node-7","node-8","paymentservice","paymentservice-0","paymentservice-1","paymentservice-2","productcatalogservice","productcatalogservice-0","productcatalogservice-1","productcatalogservice-2","recommendationservice","recommendationservice-0","recommendationservice-1","recommendationservice-2","redis","redis-cart","redis-cart-0","shippingservice","shippingservice-0","shippingservice-1","shippingservice-2","tidb-pd","tidb-tidb","tidb-tikv"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[13.594,40.781,67.969,95.156,122.344,149.531,176.719,203.906,231.094,258.281,285.469,312.656,339.844,367.031,394.219,421.406,448.594,475.781,502.969,530.156,557.344,584.531,611.719,638.906,666.094,693.281,720.469,747.656,774.844,802.031,829.219,856.406,883.594,910.781,937.969,965.156,992.344,1019.531,1046.719,1073.906,1101.094,1128.281,1155.469,1182.656,1209.844,1237.031,1264.219,1291.406,1318.594,1345.781,1372.969,1400.156,1427.344,1454.531,1481.719,1508.906,1536.094,1563.281,1590.469,1617.656,1644.844,1672.031,1699.219,1726.406]
[M1] rank=1 service=adservice-0 metric=pod_memory_working_set_bytes baseline=6.338667 peak=12808525.31 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,95.08,-95.08,0,0,0,0,0,0,0,0,0,0,0,0,0,12808525.31,-12808525.31,9306579.93,-9306579.93,0,0,0,0,0,0,0,8980539.88
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M2] rank=2 service=currencyservice-1 metric=pod_memory_working_set_bytes baseline=1450.056 peak=571418.82 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:1304.76,192.83,329.62,-85.16,-378.4,281.29,-1018.24,336.12,628.9,-866.92,665.74,1141.1,-1265.65,418.65,-92.85,569827.03,-571145.61,-102.73,112.52,43.43,47.31,308.93,-9.34,-298.62,211.53,742.87,-690.13,333.4,327.15,-706.62
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M3] rank=3 service=emailservice-2 metric=pod_memory_working_set_bytes baseline=6.47 peak=852969.19 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,97.05,852872.14,-852969.19,0,0,0,0,0,0,0,0,0,0,0,75.57,-75.57
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M4] rank=4 service=node-2 metric=node_filesystem_usage_rate baseline=29.86 peak=29.865 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:29.86,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.005
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M5] rank=5 service=node-7 metric=node_network_receive_bytes_total baseline=164.07 peak=164.09 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:164.07,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.02,-0.02,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M6] rank=6 service=tidb-tidb metric=duration_avg baseline=0.0 peak=0.01 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.01,0,-0.01,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M7] rank=7 service=tidb-tidb metric=duration_99th baseline=0.01 peak=0.02 signed_z=500.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.01,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.01,-0.01,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M8] rank=8 service=tidb-tikv metric=write_wal_mbps baseline=5.356667 peak=2219.52 signed_z=342.112 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:10.44,-10.44,1.04,9.4,1.05,-11.49,0,2.04,-2.04,20.89,-20.89,1.04,9.4,2.09,-12.53,2219.52,-1692.16,-136.47,-390.89,11.49,342.53,-340.44,-13.58,56.64,-45.15,-1.05,-10.44,376.91,-362.33,105.46
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M9] rank=9 service=k8s-master2 metric=node_filesystem_free_bytes baseline=9247218346.666666 peak=9375252480.0 signed_z=195.241 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:9247780864,-8192,0,-8192,-8192,192512,-401408,-462848,0,0,0,0,-139264,-1163264,0,0,-995328,-49152,0,-2097152,0,-20480,20480,0,-151552,-110592,-20480,200704,0,132694016
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M10] rank=10 service=tidb-tidb metric=block_cache_size baseline=3131926.4 peak=5588400.0 signed_z=152.205 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:3112160,0,0,0,0,0,32944,0,0,0,0,0,0,0,0,2245632,0,164720,0,0,0,0,0,32944,0,0,0,0,0,0
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M11] rank=11 service=k8s-master2 metric=node_filesystem_usage_rate baseline=35.662667 peak=35.415 signed_z=-99.288 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:35.66,0,0,0,0,0,0,0.005,0,0,0,0,0,0,0,0,0,0,0,0.005,0,0,0,0,0,0,0,0,0,-0.255
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M12] rank=12 service=k8s-master3 metric=node_filesystem_usage_rate baseline=68.611333 peak=68.35 signed_z=-76.878 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:68.61,0,0,0,0,0,0,0,0,0,0,0,0,0.01,0,0,0,0.01,0,-0.01,0,-0.25,-0.01,0,0,0,0,0.01,-0.02,0
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[1020.0,1140.0]

=== LOG SUMMARY ===
{"entries":[{"change_pct":-100.0,"n_during":0,"n_pre":20,"service":"redis-cart-0"},{"change_pct":-93.8,"n_during":3,"n_pre":48,"service":"emailservice-1"},{"change_pct":-93.8,"n_during":6,"n_pre":96,"service":"paymentservice-2"},{"change_pct":-93.2,"n_during":146,"n_pre":2159,"service":"adservice-2"},{"change_pct":-93.2,"n_during":2007,"n_pre":29322,"service":"cartservice-1"},{"change_pct":-93.2,"n_during":1608,"n_pre":23571,"service":"currencyservice-2"},{"change_pct":-93.1,"n_during":222,"n_pre":3219,"service":"frontend-1"},{"change_pct":-93.1,"n_during":380,"n_pre":5529,"service":"frontend-2"}],"mode":"volume","omitted_services":14,"service_count":22}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":-12.1,"error_pct":0.0,"p95_during_ms":0.9530000000000001,"p95_pre_ms":1.084,"service":"emailservice","spans":152},{"delta_pct":11.3,"error_pct":0.0,"p95_during_ms":163.12304999999992,"p95_pre_ms":146.55039999999994,"service":"checkoutservice","spans":1798},{"delta_pct":-7.0,"error_pct":0.0,"p95_during_ms":4.3235,"p95_pre_ms":4.647,"service":"recommendationservice","spans":5532},{"delta_pct":4.1,"error_pct":0.0,"p95_during_ms":0.5441000000000001,"p95_pre_ms":0.5224499999999996,"service":"shippingservice","spans":1072},{"delta_pct":2.2,"error_pct":0.0,"p95_during_ms":2.4064999999999994,"p95_pre_ms":2.3551999999999933,"service":"redis","spans":3991},{"delta_pct":1.6,"error_pct":0.0,"p95_during_ms":3.921999999999999,"p95_pre_ms":3.862,"service":"cartservice","spans":3684},{"delta_pct":1.0,"error_pct":0.0,"p95_during_ms":13.610499999999996,"p95_pre_ms":13.48075,"service":"productcatalogservice","spans":20829},{"delta_pct":0.7,"error_pct":0.0,"p95_during_ms":88.917,"p95_pre_ms":88.28,"service":"frontend","spans":45035}],"omitted_services":0,"service_count":8}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=7 omitted_edges=0
[{"evidence_source":"metric","onset_rel_s":900.0,"rank":1,"service":"currencyservice","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":900.0,"rank":2,"service":"emailservice","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":900.0,"rank":3,"service":"node-7","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":900.0,"rank":4,"service":"tidb-tidb","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":900.0,"rank":5,"service":"tidb-tikv","severity_z":342.112},{"evidence_source":"metric","onset_rel_s":1020.0,"rank":6,"service":"redis-cart","severity_z":15.359},{"evidence_source":"metric","onset_rel_s":1080.0,"rank":7,"service":"adservice","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1200.0,"rank":8,"service":"shippingservice","severity_z":54.191},{"evidence_source":"metric","onset_rel_s":1260.0,"rank":9,"service":"k8s-master3","severity_z":76.878},{"evidence_source":"metric","onset_rel_s":1740.0,"rank":10,"service":"node-2","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1740.0,"rank":11,"service":"k8s-master2","severity_z":195.241},{"evidence_source":"metric","onset_rel_s":1740.0,"rank":12,"service":"cartservice","severity_z":45.323},{"evidence_source":"none","onset_rel_s":null,"rank":13,"service":"checkoutservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":14,"service":"frontend","severity_z":0.0}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"cartservice","caller":"checkoutservice"},{"callee":"emailservice","caller":"checkoutservice"},{"callee":"shippingservice","caller":"checkoutservice"},{"callee":"cartservice","caller":"frontend"},{"callee":"checkoutservice","caller":"frontend"},{"callee":"shippingservice","caller":"frontend"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

{"confidence":"medium","reason":"Rank tidb-tikv first because tidb-tikv has direct write_wal_mbps evidence (signed-z 342.11, persistence 0 bins); currencyservice is second despite propagation rank 1 because onset ordering alone does not establish the causal origin.","services":["tidb-tikv","currencyservice"]}

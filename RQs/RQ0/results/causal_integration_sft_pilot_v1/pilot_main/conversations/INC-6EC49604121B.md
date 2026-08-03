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
opaque_id: INC-6EC49604121B
observation_window={"duration_rel_s":1740.0,"source_metric_rows":30}
selection_summary={"candidate_count":60,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":497,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["adservice","adservice-0","adservice-1","adservice-2","cartservice","cartservice-0","cartservice-1","cartservice-2","checkoutservice","checkoutservice-0","checkoutservice-1","checkoutservice-2","currencyservice","currencyservice-0","currencyservice-1","currencyservice-2","emailservice","emailservice-0","emailservice-1","emailservice-2","example-ant-10-29159520-nlwlw","example-ant-29159520-w5hmd","frontend","frontend-0","frontend-1","frontend-2","hipstershop","k8s-master1","k8s-master2","k8s-master3","node-1","node-2","node-3","node-4","node-5","node-6","node-7","node-8","paymentservice","paymentservice-0","paymentservice-1","paymentservice-2","productcatalogservice","productcatalogservice-0","productcatalogservice-1","productcatalogservice-2","recommendationservice","recommendationservice-0","recommendationservice-1","recommendationservice-2","redis","redis-cart","redis-cart-0","shippingservice","shippingservice-0","shippingservice-1","shippingservice-2","tidb-pd","tidb-tidb","tidb-tikv"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[13.594,40.781,67.969,95.156,122.344,149.531,176.719,203.906,231.094,258.281,285.469,312.656,339.844,367.031,394.219,421.406,448.594,475.781,502.969,530.156,557.344,584.531,611.719,638.906,666.094,693.281,720.469,747.656,774.844,802.031,829.219,856.406,883.594,910.781,937.969,965.156,992.344,1019.531,1046.719,1073.906,1101.094,1128.281,1155.469,1182.656,1209.844,1237.031,1264.219,1291.406,1318.594,1345.781,1372.969,1400.156,1427.344,1454.531,1481.719,1508.906,1536.094,1563.281,1590.469,1617.656,1644.844,1672.031,1699.219,1726.406]
[M1] rank=1 service=k8s-master1 metric=node_filesystem_usage_rate baseline=47.435 peak=47.4 signed_z=-999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:47.435,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,-0.03,0,-0.005,0.005,0,0,0,0,0.005,0,0,0,0,0
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M2] rank=2 service=node-7 metric=node_network_receive_bytes_total baseline=164.07 peak=159.67 signed_z=-999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:164.07,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,-4.4,4.4,0,0,0
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M3] rank=3 service=node-7 metric=node_network_receive_packets_total baseline=1.6 peak=1.53 signed_z=-999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:1.6,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,-0.07,0.07,0,0,0
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M4] rank=4 service=node-7 metric=node_network_transmit_packets_total baseline=1.6 peak=1.53 signed_z=-999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:1.6,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,-0.07,0.07,0,0,0
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M5] rank=5 service=tidb-tidb metric=duration_99th baseline=0.01 peak=0.02 signed_z=500.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.01,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.01,0,0,0,0,0,0,0,0,0,-0.01,0,0,0
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M6] rank=6 service=node-7 metric=node_cpu_usage_rate baseline=18.468 peak=96.45 signed_z=71.144 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:18.56,-0.23,1.86,-3.94,1.77,-0.61,2.06,-0.99,-1.21,1.87,-0.87,1,1.25,-3.05,0.9,10.11,67.97,-7.03,4.42,-6.5,3.61,-1.4,-3.89,6.5,-5.11,-9.12,-59.55,3.84,-3.96,-0.28
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M7] rank=7 service=emailservice metric=rrt_max baseline=6365.466667 peak=67928.0 signed_z=39.392 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:4799,2293,-812,-838,769,2511,-1109,718,-4863,986,2383,-1611,1029,-636,3514,-3960,62755,-62566,-1178,104,964,-1317,792,2029,-2725,660,6069,-5595,-118,-868
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M8] rank=8 service=k8s-master1 metric=node_filesystem_free_bytes baseline=4908388352.0 peak=4926513152.0 signed_z=37.336 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:4908531712,0,28672,-118784,-237568,0,4096,-20480,172032,-217088,0,-20480,0,1966080,-2109440,131072,16375808,-233472,2260992,-2052096,-208896,-12288,-434176,0,-2011136,-479232,0,36864,0,356352
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M9] rank=9 service=emailservice-1 metric=rrt_max baseline=4867.0 peak=67928.0 signed_z=32.916 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:3747,-474,3007,-3260,3191,-2310,-1105,5535,-5134,1257,-445,1217,1029,-3083,5961,-5250,64045,-64554,810,-999,-391,391,1542,-481,-1121,685,-767,434,233,-512
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M10] rank=10 service=productcatalogservice-0 metric=rrt_max baseline=35508.866667 peak=145030.0 signed_z=19.696 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:33837,-9315,17969,-3419,4207,-3556,-1826,-6293,10963,-12468,10237,-4649,-5953,1988,-1659,10009,20352,3286,11585,69735,-74898,21654,-15230,42259,-22222,-65724,-1524,-2074,4867,7677
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M11] rank=11 service=productcatalogservice metric=rrt_max baseline=35508.866667 peak=145030.0 signed_z=19.696 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:33837,-9315,17969,-3419,4207,-3556,-1826,-6293,10963,-12468,10237,-4649,-5953,1988,-1659,10009,20352,3286,11585,69735,-74898,21654,-15230,42259,-22222,-65724,-1524,4273,-1480,7677
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M12] rank=12 service=tidb-pd metric=cpu_usage baseline=0.792 peak=0.65 signed_z=-15.618 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.8,-0.02,0,0.02,0,-0.01,0,-0.01,0.01,0.02,-0.01,-0.02,0.01,0.01,-0.01,-0.01,-0.13,0.05,0.01,0.01,-0.02,0.02,-0.03,0.02,0.03,-0.01,0.06,0,0.01,-0.02
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[900.0,1740.0]

=== LOG SUMMARY ===
{"entries":[{"change_pct":-26.5,"n_during":5929,"n_pre":8072,"service":"frontend-2"},{"change_pct":-18.7,"n_during":14372,"n_pre":17687,"service":"currencyservice-0"},{"change_pct":-18.1,"n_during":531,"n_pre":648,"service":"checkoutservice-0"},{"change_pct":-18.0,"n_during":464,"n_pre":566,"service":"currencyservice-2"},{"change_pct":-17.8,"n_during":3188,"n_pre":3876,"service":"recommendationservice-2"},{"change_pct":-17.5,"n_during":1440,"n_pre":1746,"service":"cartservice-1"},{"change_pct":-17.5,"n_during":80,"n_pre":97,"service":"emailservice-0"},{"change_pct":-17.5,"n_during":80,"n_pre":97,"service":"emailservice-2"}],"mode":"volume","omitted_services":16,"service_count":24}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":9.3,"error_pct":0.0,"p95_during_ms":15.33,"p95_pre_ms":14.03165,"service":"productcatalogservice","spans":70406},{"delta_pct":-8.8,"error_pct":0.0,"p95_during_ms":0.3935,"p95_pre_ms":0.43159999999999943,"service":"shippingservice","spans":3633},{"delta_pct":-7.9,"error_pct":0.0,"p95_during_ms":130.66160000000008,"p95_pre_ms":141.941,"service":"checkoutservice","spans":6124},{"delta_pct":-7.3,"error_pct":0.0,"p95_during_ms":2.379599999999991,"p95_pre_ms":2.566,"service":"redis","spans":13506},{"delta_pct":-3.9,"error_pct":0.0,"p95_during_ms":84.26579999999981,"p95_pre_ms":87.64825,"service":"frontend","spans":152064},{"delta_pct":-3.8,"error_pct":0.0,"p95_during_ms":3.794,"p95_pre_ms":3.9430999999999985,"service":"cartservice","spans":12461},{"delta_pct":-1.6,"error_pct":0.0,"p95_during_ms":4.996549999999999,"p95_pre_ms":5.076,"service":"recommendationservice","spans":18708},{"delta_pct":1.0,"error_pct":0.0,"p95_during_ms":1.007,"p95_pre_ms":0.9969999999999999,"service":"emailservice","spans":518}],"omitted_services":0,"service_count":8}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=6 omitted_edges=0
[{"evidence_source":"metric","onset_rel_s":960.0,"rank":1,"service":"k8s-master1","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":960.0,"rank":2,"service":"tidb-tidb","severity_z":500.0},{"evidence_source":"metric","onset_rel_s":960.0,"rank":3,"service":"emailservice","severity_z":39.392},{"evidence_source":"metric","onset_rel_s":960.0,"rank":4,"service":"tidb-pd","severity_z":15.618},{"evidence_source":"metric","onset_rel_s":1020.0,"rank":5,"service":"cartservice","severity_z":10.19},{"evidence_source":"metric","onset_rel_s":1140.0,"rank":6,"service":"productcatalogservice","severity_z":19.696},{"evidence_source":"metric","onset_rel_s":1500.0,"rank":7,"service":"node-7","severity_z":999.0},{"evidence_source":"none","onset_rel_s":null,"rank":8,"service":"checkoutservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":9,"service":"currencyservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":10,"service":"hipstershop","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":11,"service":"frontend","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":12,"service":"recommendationservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":13,"service":"redis-cart","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":14,"service":"tidb-tikv","severity_z":0.0}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"cartservice","caller":"checkoutservice"},{"callee":"emailservice","caller":"checkoutservice"},{"callee":"productcatalogservice","caller":"checkoutservice"},{"callee":"cartservice","caller":"frontend"},{"callee":"checkoutservice","caller":"frontend"},{"callee":"productcatalogservice","caller":"frontend"},{"callee":"recommendationservice","caller":"frontend"},{"callee":"productcatalogservice","caller":"recommendationservice"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

{"confidence":"medium","reason":"Rank node-7 first because node-7 has direct node_network_receive_bytes_total evidence (signed-z -999, persistence 0 bins); k8s-master1 is second despite propagation rank 1 because onset ordering alone does not establish the causal origin.","services":["node-7","k8s-master1"]}

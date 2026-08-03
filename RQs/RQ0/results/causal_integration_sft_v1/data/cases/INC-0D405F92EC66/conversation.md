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
opaque_id: INC-0D405F92EC66
observation_window={"duration_rel_s":1740.0,"source_metric_rows":30}
selection_summary={"candidate_count":60,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":479,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["adservice","adservice-0","adservice-1","adservice-2","cartservice","cartservice-0","cartservice-1","cartservice-2","checkoutservice","checkoutservice-0","checkoutservice-1","checkoutservice-2","currencyservice","currencyservice-0","currencyservice-1","currencyservice-2","emailservice","emailservice-0","emailservice-1","emailservice-2","example-ant-10-29173920-kh429","example-ant-29173920-v886k","frontend","frontend-0","frontend-1","frontend-2","hipstershop","k8s-master1","k8s-master2","k8s-master3","node-1","node-2","node-3","node-4","node-5","node-6","node-7","node-8","paymentservice","paymentservice-0","paymentservice-1","paymentservice-2","productcatalogservice","productcatalogservice-0","productcatalogservice-1","productcatalogservice-2","recommendationservice","recommendationservice-0","recommendationservice-1","recommendationservice-2","redis","redis-cart","redis-cart-0","shippingservice","shippingservice-0","shippingservice-1","shippingservice-2","tidb-pd","tidb-tidb","tidb-tikv"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[13.594,40.781,67.969,95.156,122.344,149.531,176.719,203.906,231.094,258.281,285.469,312.656,339.844,367.031,394.219,421.406,448.594,475.781,502.969,530.156,557.344,584.531,611.719,638.906,666.094,693.281,720.469,747.656,774.844,802.031,829.219,856.406,883.594,910.781,937.969,965.156,992.344,1019.531,1046.719,1073.906,1101.094,1128.281,1155.469,1182.656,1209.844,1237.031,1264.219,1291.406,1318.594,1345.781,1372.969,1400.156,1427.344,1454.531,1481.719,1508.906,1536.094,1563.281,1590.469,1617.656,1644.844,1672.031,1699.219,1726.406]
[M1] rank=1 service=node-7 metric=node_network_receive_bytes_total baseline=164.07 peak=146.47 signed_z=-999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:164.07,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,-17.6,17.6
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M2] rank=2 service=node-7 metric=node_network_receive_packets_total baseline=1.6 peak=1.33 signed_z=-999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:1.6,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,-0.27,0.27
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M3] rank=3 service=node-7 metric=node_network_transmit_packets_total baseline=1.6 peak=1.33 signed_z=-999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:1.6,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,-0.27,0.27
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M4] rank=4 service=shippingservice-2 metric=pod_memory_working_set_bytes baseline=7.063333 peak=287613.69 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,105.95,-105.95,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,287613.69,-287613.69,0,0,0,0,0,0,0,0
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M5] rank=5 service=k8s-master1 metric=node_disk_write_time_seconds_total baseline=0.019333 peak=0.29 signed_z=29.149 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.01,0,0.01,0,-0.01,0.02,-0.02,0.02,-0.01,-0.01,0,0.03,-0.02,0,0.01,0,0.03,0.23,-0.08,-0.02,0.05,0.03,-0.02,-0.03,-0.05,-0.13,0,-0.02,-0.01,0
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M6] rank=6 service=currencyservice-1 metric=rrt_max baseline=2944.466667 peak=31739.0 signed_z=29.027 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:3432,-1453,699,-304,-448,3461,-2118,-759,-734,219,2106,-1107,1346,-1973,672,-893,29593,-23505,-5117,-669,-242,712,-1131,81,167,1419,-1176,-320,367,48
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M7] rank=7 service=currencyservice-1 metric=rrt baseline=1305.266667 peak=3292.36 signed_z=21.253 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:1433.17,-155.58,80.91,-60.92,-89.72,167.46,-32.99,-204.73,126.19,-122.5,179.21,55.22,-28.4,-114.6,234.99,-198.06,2022.71,-1971.12,13.61,-90.05,-134.11,206.38,-135.03,148.36,150.77,-54.47,80.03,-240.11,-52.34,94.08
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M8] rank=8 service=node-3 metric=node_memory_usage_rate baseline=67.507333 peak=48.38 signed_z=-20.731 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:66.42,0.96,-0.06,-0.72,-0.05,0.14,1.46,-0.08,0.01,-1.57,0.45,2.11,-0.06,-0.17,-1.88,0.33,-18.91,0.24,0.1,-0.08,0.43,0.24,0.07,0.14,0,-0.2,0.58,0.22,-0.05,-0.09
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M9] rank=9 service=node-3 metric=node_memory_MemAvailable_bytes baseline=4873960379.733334 peak=8082026496.0 signed_z=20.709 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:5056638976,-160833536,9265152,121147392,7602176,-22798336,-244637696,13004800,-1470464,263823360,-75681792,-354541568,9850880,28839936,316030976,-56651776,3172438016,-40706048,-16715776,13291520,-72007680,-39743488,-12460032,-23031808,-925696,33853440,-97947648,-36732928,9326592,14188544
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M10] rank=10 service=shippingservice-2 metric=rrt_max baseline=3094.666667 peak=14781.0 signed_z=14.555 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:3927,41,-1036,-647,-945,1720,1234,-376,-1294,727,306,-1010,256,650,-1592,6644,-6680,-264,-316,4017,2936,6483,-13169,560,-463,2143,-1939,160,5463,-5859
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M11] rank=11 service=paymentservice-1 metric=rrt_max baseline=2276.866667 peak=9680.0 signed_z=11.157 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:3016,-1185,102,586,-731,1907,-39,-1415,236,-627,-241,341,244,-304,-386,-109,421,7864,-7905,493,-699,574,-386,98,255,310,-1124,2090,-1581,971
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M12] rank=12 service=node-7 metric=node_network_transmit_bytes_total baseline=5532.275333 peak=5513.87 signed_z=-8.746 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:5534.67,-4.74,-1.13,3.67,1.26,0.54,-5.67,3.07,1.93,0.13,-3.6,4.6,-1.53,1.07,-3.94,7.54,-6.07,-1.67,2,-1.46,0.4,-0.47,1.33,2.87,-0.8,-0.53,-2.74,4,-20.86,14.86
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[1620.0,1740.0]

=== LOG SUMMARY ===
{"entries":[{"change_pct":-100.0,"n_during":0,"n_pre":28,"service":"redis-cart-0"},{"change_pct":-93.3,"n_during":10,"n_pre":149,"service":"emailservice-0"},{"change_pct":-93.3,"n_during":20,"n_pre":298,"service":"paymentservice-2"},{"change_pct":-93.2,"n_during":58,"n_pre":858,"service":"currencyservice-1"},{"change_pct":-93.0,"n_during":183,"n_pre":2600,"service":"recommendationservice-0"},{"change_pct":-92.9,"n_during":189,"n_pre":2664,"service":"cartservice-1"},{"change_pct":-92.9,"n_during":778,"n_pre":10968,"service":"frontend-1"},{"change_pct":-92.9,"n_during":42,"n_pre":594,"service":"shippingservice-1"}],"mode":"volume","omitted_services":15,"service_count":23}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":-23.6,"error_pct":0.0,"p95_during_ms":2.043449999999999,"p95_pre_ms":2.6742999999999992,"service":"redis","spans":11917},{"delta_pct":-21.2,"error_pct":0.0,"p95_during_ms":3.3137999999999983,"p95_pre_ms":4.207099999999997,"service":"cartservice","spans":11002},{"delta_pct":14.3,"error_pct":0.0,"p95_during_ms":1.1468999999999998,"p95_pre_ms":1.00355,"service":"emailservice","spans":462},{"delta_pct":-5.2,"error_pct":0.0,"p95_during_ms":137.93399999999997,"p95_pre_ms":145.47854999999998,"service":"checkoutservice","spans":5436},{"delta_pct":-4.5,"error_pct":0.0,"p95_during_ms":4.4963500000000005,"p95_pre_ms":4.710449999999999,"service":"recommendationservice","spans":16466},{"delta_pct":1.9,"error_pct":0.0,"p95_during_ms":0.4695999999999999,"p95_pre_ms":0.461,"service":"shippingservice","spans":3217},{"delta_pct":-1.4,"error_pct":0.0,"p95_during_ms":13.250250000000001,"p95_pre_ms":13.439,"service":"productcatalogservice","spans":61976},{"delta_pct":-1.2,"error_pct":0.0,"p95_during_ms":83.9,"p95_pre_ms":84.96034999999995,"service":"frontend","spans":134479}],"omitted_services":0,"service_count":8}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=7 omitted_edges=0
[{"evidence_source":"metric","onset_rel_s":960.0,"rank":1,"service":"currencyservice","severity_z":29.027},{"evidence_source":"metric","onset_rel_s":960.0,"rank":2,"service":"node-3","severity_z":20.731},{"evidence_source":"metric","onset_rel_s":1020.0,"rank":3,"service":"k8s-master1","severity_z":29.149},{"evidence_source":"metric","onset_rel_s":1020.0,"rank":4,"service":"paymentservice","severity_z":11.157},{"evidence_source":"metric","onset_rel_s":1200.0,"rank":5,"service":"shippingservice","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1680.0,"rank":6,"service":"node-7","severity_z":999.0},{"evidence_source":"none","onset_rel_s":null,"rank":7,"service":"productcatalogservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":8,"service":"tidb-tikv","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":9,"service":"tidb-tidb","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":10,"service":"cartservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":11,"service":"frontend","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":12,"service":"emailservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":13,"service":"checkoutservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":14,"service":"example-ant","severity_z":0.0}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"cartservice","caller":"checkoutservice"},{"callee":"emailservice","caller":"checkoutservice"},{"callee":"productcatalogservice","caller":"checkoutservice"},{"callee":"shippingservice","caller":"checkoutservice"},{"callee":"cartservice","caller":"frontend"},{"callee":"checkoutservice","caller":"frontend"},{"callee":"productcatalogservice","caller":"frontend"},{"callee":"shippingservice","caller":"frontend"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

[excluded before optimizer]

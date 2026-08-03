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
opaque_id: INC-B10955A910AF
observation_window={"duration_rel_s":1740.0,"source_metric_rows":30}
selection_summary={"candidate_count":60,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":490,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["adservice","adservice-0","adservice-1","adservice-2","cartservice","cartservice-0","cartservice-1","cartservice-2","checkoutservice","checkoutservice-0","checkoutservice-1","checkoutservice-2","currencyservice","currencyservice-0","currencyservice-1","currencyservice-2","emailservice","emailservice-0","emailservice-1","emailservice-2","example-ant-10-29169600-zkv48","example-ant-29169600-8lqgx","frontend","frontend-0","frontend-1","frontend-2","hipstershop","k8s-master1","k8s-master2","k8s-master3","node-1","node-2","node-3","node-4","node-5","node-6","node-7","node-8","paymentservice","paymentservice-0","paymentservice-1","paymentservice-2","productcatalogservice","productcatalogservice-0","productcatalogservice-1","productcatalogservice-2","recommendationservice","recommendationservice-0","recommendationservice-1","recommendationservice-2","redis","redis-cart","redis-cart-0","shippingservice","shippingservice-0","shippingservice-1","shippingservice-2","tidb-pd","tidb-tidb","tidb-tikv"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[13.594,40.781,67.969,95.156,122.344,149.531,176.719,203.906,231.094,258.281,285.469,312.656,339.844,367.031,394.219,421.406,448.594,475.781,502.969,530.156,557.344,584.531,611.719,638.906,666.094,693.281,720.469,747.656,774.844,802.031,829.219,856.406,883.594,910.781,937.969,965.156,992.344,1019.531,1046.719,1073.906,1101.094,1128.281,1155.469,1182.656,1209.844,1237.031,1264.219,1291.406,1318.594,1345.781,1372.969,1400.156,1427.344,1454.531,1481.719,1508.906,1536.094,1563.281,1590.469,1617.656,1644.844,1672.031,1699.219,1726.406]
[M1] rank=1 service=tidb-tidb metric=duration_avg baseline=0.0 peak=0.05 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.05,0,-0.05,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M2] rank=2 service=tidb-tidb metric=duration_99th baseline=0.01 peak=5.53 signed_z=998.192 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.01,0,0,0,0,0,0,0,0,0,0,0,0,0,0,5.52,-5.52,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M3] rank=3 service=tidb-tidb metric=block_cache_size baseline=52023632.0 peak=3440384.0 signed_z=-933.869 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:52023632,0,0,0,0,0,0,0,0,0,0,0,0,0,0,-48583248,0,0,0,560048,0,0,0,189296,32944,0,32944,0,0,0
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M4] rank=4 service=currencyservice-1 metric=pod_memory_working_set_bytes baseline=2831.57 peak=974761.29 signed_z=739.92 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:3179.49,1036.98,555.27,679.86,-2513.83,-2208.72,1227.29,-140.31,806.15,-1095.96,291.09,-148.88,1559.67,1121.2,-2145.78,5072.93,-3461.05,383.92,-827.91,784.54,-1489.63,412.67,1604.68,-1518.98,825719.62,-143079.88,-683954.64,-102.98,-554.23,973568.71
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M5] rank=5 service=tidb-tikv metric=memory_usage baseline=2075110604.8 peak=1965285376.0 signed_z=-263.783 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:2075181056,856064,-303104,-413696,-487424,114688,-53248,-200704,462848,102400,-569344,-77824,380928,667648,-1011712,-109355008,503808,-512000,1024000,1929216,585728,208896,528384,-352256,2449408,-901120,376832,561152,151552,-237568
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M6] rank=6 service=tidb-tikv metric=region_pending baseline=148702.466667 peak=479.0 signed_z=-178.234 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:147189,131,704,129,138,132,160,136,134,130,128,127,129,705,139,-149732,141,139,127,143,138,140,133,135,708,128,157,133,130,138
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M7] rank=7 service=currencyservice-2 metric=rrt_max baseline=6655.8 peak=68723.0 signed_z=46.22 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:8344,-3311,971,-726,2533,-1544,-51,2294,92,-3568,767,2206,-2622,2712,-2649,3629,59646,-64062,-633,9120,-6178,1939,-3769,1747,265,-1677,-679,2582,-603,-425
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M8] rank=8 service=node-2 metric=node_network_transmit_bytes_total baseline=2395.88 peak=2478.13 signed_z=32.554 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:2397.2,-3.27,0.94,-0.47,-0.93,1.06,0.47,2,-2.33,-3,9.06,-4.33,-0.8,6,-4.47,0.87,80.13,-87.06,2.4,-0.87,4.13,-0.93,-2,7.47,-3.34,-6.53,1.6,5.6,2.47,-2.47
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M9] rank=9 service=node-5 metric=node_network_transmit_bytes_total baseline=5254.78 peak=5329.73 signed_z=30.472 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:5255.13,-3.26,2.2,1.4,-0.54,-1.06,6.93,-7.8,-1.47,8.07,-5.87,0.77,-1.9,2.13,1.14,-2.27,2.13,-2.13,0.33,0.14,1.46,1.6,-1.26,-3.6,1.53,1.8,2.6,-4.47,76,-76.06
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M10] rank=10 service=currencyservice metric=rrt_max baseline=7955.0 peak=68723.0 signed_z=25.394 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:8561,3071,-5628,-726,6010,-5021,-51,4315,1857,-3966,-2621,2206,-2622,2712,-2649,3629,59646,-58667,-1832,4924,-6178,1939,6317,-8339,265,-787,-903,2734,1805,-1540
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M11] rank=11 service=paymentservice-1 metric=rrt baseline=1483.561333 peak=8831.5 signed_z=20.728 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:1606,-21.5,164.67,-389.67,-168,327,-200.5,1277,-1029,-300,-25.75,390.75,-625.75,279,54.25,-77.25,-313,286.25,419.75,-457.75,122.5,474.5,955,-1443,60,-98,-306.25,7870.25,-7481.25,361.75
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M12] rank=12 service=k8s-master2 metric=node_filesystem_usage_rate baseline=35.361333 peak=35.3 signed_z=-18.043 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:35.37,0,-0.01,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.005,0,0,0,0,0,0,0,-0.065,0.07
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[840.0,1740.0]

=== LOG SUMMARY ===
{"entries":[{"change_pct":8.0,"n_during":27,"n_pre":25,"service":"emailservice-2"},{"change_pct":8.0,"n_during":54,"n_pre":50,"service":"paymentservice-0"},{"change_pct":-4.1,"n_during":1743,"n_pre":1817,"service":"frontend-2"},{"change_pct":3.9,"n_during":477,"n_pre":459,"service":"cartservice-2"},{"change_pct":3.1,"n_during":2394,"n_pre":2323,"service":"frontend-0"},{"change_pct":2.7,"n_during":150,"n_pre":146,"service":"currencyservice-0"},{"change_pct":2.6,"n_during":237,"n_pre":231,"service":"checkoutservice-1"},{"change_pct":2.4,"n_during":6687,"n_pre":6529,"service":"cartservice-0"}],"mode":"volume","omitted_services":15,"service_count":23}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":13.1,"error_pct":0.0,"p95_during_ms":1.2001999999999997,"p95_pre_ms":1.0612000000000001,"service":"emailservice","spans":156},{"delta_pct":-7.7,"error_pct":0.0,"p95_during_ms":0.4822,"p95_pre_ms":0.5226,"service":"shippingservice","spans":1094},{"delta_pct":-7.4,"error_pct":0.0,"p95_during_ms":3.0070499999999987,"p95_pre_ms":3.247599999999998,"service":"redis","spans":4031},{"delta_pct":2.9,"error_pct":0.0,"p95_during_ms":16.6708,"p95_pre_ms":16.202700000000004,"service":"productcatalogservice","spans":20899},{"delta_pct":2.7,"error_pct":0.0,"p95_during_ms":89.5462,"p95_pre_ms":87.18599999999999,"service":"frontend","spans":45251},{"delta_pct":2.1,"error_pct":0.0,"p95_during_ms":6.172299999999996,"p95_pre_ms":6.0465,"service":"recommendationservice","spans":5540},{"delta_pct":-1.9,"error_pct":0.0,"p95_during_ms":125.67994999999992,"p95_pre_ms":128.152,"service":"checkoutservice","spans":1812},{"delta_pct":-0.0,"error_pct":0.0,"p95_during_ms":4.781249999999997,"p95_pre_ms":4.7816,"service":"cartservice","spans":3730}],"omitted_services":0,"service_count":8}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=10 omitted_edges=1
[{"evidence_source":"trace","onset_rel_s":852.0,"rank":1,"service":"checkoutservice","severity_z":104.599},{"evidence_source":"metric","onset_rel_s":900.0,"rank":2,"service":"tidb-tidb","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":900.0,"rank":3,"service":"tidb-tikv","severity_z":263.783},{"evidence_source":"metric","onset_rel_s":960.0,"rank":4,"service":"node-2","severity_z":32.554},{"evidence_source":"trace","onset_rel_s":1069.2,"rank":5,"service":"emailservice","severity_z":8.418},{"evidence_source":"metric","onset_rel_s":1140.0,"rank":6,"service":"node-8","severity_z":10.69},{"evidence_source":"metric","onset_rel_s":1260.0,"rank":7,"service":"node-1","severity_z":10.69},{"evidence_source":"metric","onset_rel_s":1440.0,"rank":8,"service":"currencyservice","severity_z":739.92},{"evidence_source":"trace","onset_rel_s":1468.2,"rank":9,"service":"cartservice","severity_z":11.388},{"evidence_source":"trace","onset_rel_s":1468.2,"rank":10,"service":"redis","severity_z":9.211},{"evidence_source":"metric","onset_rel_s":1620.0,"rank":11,"service":"paymentservice","severity_z":20.728},{"evidence_source":"metric","onset_rel_s":1680.0,"rank":12,"service":"node-5","severity_z":30.472},{"evidence_source":"metric","onset_rel_s":1680.0,"rank":13,"service":"k8s-master2","severity_z":18.043},{"evidence_source":"none","onset_rel_s":null,"rank":14,"service":"adservice","severity_z":0.0}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"redis","caller":"cartservice"},{"callee":"cartservice","caller":"checkoutservice"},{"callee":"emailservice","caller":"checkoutservice"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

{"confidence":"medium","reason":"Rank tidb-tikv first because tidb-tikv has direct memory_usage evidence (signed-z -263.78, persistence 0 bins); checkoutservice is second despite propagation rank 1 because onset ordering alone does not establish the causal origin. The remaining entries preserve evidence-supported alternatives so the ranking retains calibrated uncertainty instead of collapsing to one answer.","services":["tidb-tikv","tidb-tidb","checkoutservice","currencyservice-1","paymentservice-1"]}

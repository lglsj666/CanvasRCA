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
opaque_id: INC-B12C19E840D6
observation_window={"duration_rel_s":1740.0,"source_metric_rows":30}
selection_summary={"candidate_count":60,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":501,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["adservice","adservice-0","adservice-1","adservice-2","cartservice","cartservice-0","cartservice-1","cartservice-2","checkoutservice","checkoutservice-0","checkoutservice-1","checkoutservice-2","currencyservice","currencyservice-0","currencyservice-1","currencyservice-2","emailservice","emailservice-0","emailservice-1","emailservice-2","example-ant-10-29162400-r2drh","example-ant-29162400-cdnr4","frontend","frontend-0","frontend-1","frontend-2","hipstershop","k8s-master1","k8s-master2","k8s-master3","node-1","node-2","node-3","node-4","node-5","node-6","node-7","node-8","paymentservice","paymentservice-0","paymentservice-1","paymentservice-2","productcatalogservice","productcatalogservice-0","productcatalogservice-1","productcatalogservice-2","recommendationservice","recommendationservice-0","recommendationservice-1","recommendationservice-2","redis","redis-cart","redis-cart-0","shippingservice","shippingservice-0","shippingservice-1","shippingservice-2","tidb-pd","tidb-tidb","tidb-tikv"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[13.594,40.781,67.969,95.156,122.344,149.531,176.719,203.906,231.094,258.281,285.469,312.656,339.844,367.031,394.219,421.406,448.594,475.781,502.969,530.156,557.344,584.531,611.719,638.906,666.094,693.281,720.469,747.656,774.844,802.031,829.219,856.406,883.594,910.781,937.969,965.156,992.344,1019.531,1046.719,1073.906,1101.094,1128.281,1155.469,1182.656,1209.844,1237.031,1264.219,1291.406,1318.594,1345.781,1372.969,1400.156,1427.344,1454.531,1481.719,1508.906,1536.094,1563.281,1590.469,1617.656,1644.844,1672.031,1699.219,1726.406]
[M1] rank=1 service=checkoutservice-0 metric=pod_fs_reads_bytes baseline=0.0 peak=8659.62 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,8659.62,-8659.62,0,0,0,0,0,0,0,0,0
missing_mask_bits=0101010101111010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,0,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M2] rank=2 service=k8s-master2 metric=node_disk_write_time_seconds_total baseline=0.02 peak=0.01 signed_z=-999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.02,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,-0.01,0,0.01,0,0,0,0,0,0,0,-0.01
missing_mask_bits=0101010101111010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,0,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M3] rank=3 service=k8s-master2 metric=node_filesystem_usage_rate baseline=35.29 peak=35.255 signed_z=-999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:35.29,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,-0.03,0.03,0,0,0,0,-0.035,0.035
missing_mask_bits=0101010101111010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,0,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M4] rank=4 service=node-4 metric=node_disk_read_bytes_total baseline=0.0 peak=70997.33 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,2184.53,68812.8,-62805.33,6280.53,-14472.53,12561.07,-12561.07,0,0,8738.13,-8738.13,0,0,0,0
missing_mask_bits=0101010101111010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,0,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M5] rank=5 service=node-7 metric=node_network_receive_packets_total baseline=1.6 peak=1.53 signed_z=-999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:1.6,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,-0.07,0.07,0,0,0,0,0,0
missing_mask_bits=0101010101111010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,0,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M6] rank=6 service=node-7 metric=node_network_transmit_packets_total baseline=1.6 peak=1.53 signed_z=-999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:1.6,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,-0.07,0.07,0,0,0,0,0,0
missing_mask_bits=0101010101111010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,0,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M7] rank=7 service=paymentservice-2 metric=pod_memory_working_set_bytes baseline=415.449286 peak=644322.75 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:488.8,1647.16,-2135.96,1122.5,-431.41,-464.88,183.39,93.8,-503.4,133.94,-133.94,104.79,-104.79,0,4760.39,-4760.39,1017.76,-1017.76,1902.69,-1902.69,3212.87,-3212.87,1191.23,-1191.23,644322.75,-644322.75,865.96,-510.22,116.42
missing_mask_bits=0101010101111010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,0,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M8] rank=8 service=shippingservice-1 metric=pod_memory_working_set_bytes baseline=10.772143 peak=215605.07 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,150.81,-150.81,0,0,0,215605.07,-215605.07,0,0,0,0,0,0,0,0,249.89
missing_mask_bits=0101010101111010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,0,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M9] rank=9 service=tidb-tikv metric=raft_apply_wait baseline=0.0 peak=0.02 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.01,0.01,-0.02,0,0,0,0
missing_mask_bits=0101010101111010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,0,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M10] rank=10 service=example-ant-29162400-cdnr4 metric=pod_network_receive_bytes baseline=9.945 peak=2483.52 signed_z=972.135 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:7.43,5.27,-1.56,-4.46,3.67,0.91,-2.05,0.32,1.64,-0.88,5.37,-10.95,4.97,-0.26,-0.57,-1.85,-1.53,4.31,-5.35,5.43,-1.43,-8.43,6.13,-0.01,-2.29,5.75,-5.55,2479.49,-1137.59
missing_mask_bits=0101010101111010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,0,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M11] rank=11 service=node-7 metric=node_network_receive_bytes_total baseline=164.072857 peak=159.67 signed_z=-427.397 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:164.07,0,0,0,0,0,0,0,0,0,0.04,-0.04,0,0,0,0,0,0,0,0,0,-4.4,4.4,0,0,0,0,0,0
missing_mask_bits=0101010101111010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,0,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M12] rank=12 service=node-4 metric=node_memory_MemAvailable_bytes baseline=10170881755.428572 peak=2969489408.0 signed_z=-72.802 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:10335862784,-163651584,85372928,-21630976,96231424,-197083136,61497344,15130624,15941632,-164757504,5062656,4952064,-31334400,442368,-7072546816,6561341440,-12578816,-476082176,-423972864,-367747072,-11436032,-85635072,-681705472,-152911872,8396800,9101312,251072512,189362176,-31825920
missing_mask_bits=0101010101111010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,0,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[1080.0,1260.0]

=== LOG SUMMARY ===
{"entries":[{"change_pct":-89.9,"n_during":212,"n_pre":2097,"service":"adservice-1"},{"change_pct":-89.9,"n_during":253,"n_pre":2513,"service":"recommendationservice-2"},{"change_pct":-89.6,"n_during":2655,"n_pre":25623,"service":"cartservice-2"},{"change_pct":-89.5,"n_during":771,"n_pre":7371,"service":"frontend-1"},{"change_pct":-89.4,"n_during":5,"n_pre":47,"service":"emailservice-2"},{"change_pct":-89.4,"n_during":10,"n_pre":94,"service":"paymentservice-1"},{"change_pct":-88.8,"n_during":238,"n_pre":2122,"service":"frontend-2"},{"change_pct":-88.6,"n_during":178,"n_pre":1560,"service":"shippingservice-0"}],"mode":"volume","omitted_services":15,"service_count":23}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":-26.6,"error_pct":0.0,"p95_during_ms":0.3541999999999999,"p95_pre_ms":0.4825499999999979,"service":"shippingservice","spans":1057},{"delta_pct":8.1,"error_pct":0.0,"p95_during_ms":4.603999999999998,"p95_pre_ms":4.257249999999999,"service":"cartservice","spans":3625},{"delta_pct":6.9,"error_pct":0.0,"p95_during_ms":151.50555,"p95_pre_ms":141.6688499999999,"service":"checkoutservice","spans":1782},{"delta_pct":2.9,"error_pct":0.0,"p95_during_ms":5.182,"p95_pre_ms":5.038249999999999,"service":"recommendationservice","spans":5438},{"delta_pct":-1.9,"error_pct":0.0,"p95_during_ms":1.0088,"p95_pre_ms":1.0281999999999998,"service":"emailservice","spans":151},{"delta_pct":-0.8,"error_pct":0.0,"p95_during_ms":86.40549999999998,"p95_pre_ms":87.072,"service":"frontend","spans":44320},{"delta_pct":0.3,"error_pct":0.0,"p95_during_ms":13.7811,"p95_pre_ms":13.741200000000001,"service":"productcatalogservice","spans":20467},{"delta_pct":0.3,"error_pct":0.0,"p95_during_ms":2.77,"p95_pre_ms":2.76175,"service":"redis","spans":3927}],"omitted_services":0,"service_count":8}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=9 omitted_edges=2
[{"evidence_source":"metric","onset_rel_s":960.0,"rank":1,"service":"node-4","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1140.0,"rank":2,"service":"checkoutservice","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1140.0,"rank":3,"service":"k8s-master2","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1140.0,"rank":4,"service":"shippingservice","severity_z":999.0},{"evidence_source":"trace","onset_rel_s":1178.4,"rank":5,"service":"redis","severity_z":6.328},{"evidence_source":"trace","onset_rel_s":1178.4,"rank":6,"service":"cartservice","severity_z":6.077},{"evidence_source":"metric","onset_rel_s":1320.0,"rank":7,"service":"node-7","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1380.0,"rank":8,"service":"tidb-tikv","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1380.0,"rank":9,"service":"node-8","severity_z":12.712},{"evidence_source":"metric","onset_rel_s":1500.0,"rank":10,"service":"paymentservice","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1680.0,"rank":11,"service":"example-ant","severity_z":972.135},{"evidence_source":"metric","onset_rel_s":1680.0,"rank":12,"service":"emailservice","severity_z":12.118},{"evidence_source":"metric","onset_rel_s":1740.0,"rank":13,"service":"adservice","severity_z":10.37},{"evidence_source":"none","onset_rel_s":null,"rank":14,"service":"currencyservice","severity_z":0.0}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"redis","caller":"cartservice"},{"callee":"cartservice","caller":"checkoutservice"},{"callee":"emailservice","caller":"checkoutservice"},{"callee":"shippingservice","caller":"checkoutservice"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

{"confidence":"medium","reason":"Rank node-4 first because node-4 has direct node_disk_read_bytes_total evidence (signed-z 999, persistence 0 bins); checkoutservice is second despite propagation rank 2 because onset ordering alone does not establish the causal origin.","services":["node-4","checkoutservice"]}

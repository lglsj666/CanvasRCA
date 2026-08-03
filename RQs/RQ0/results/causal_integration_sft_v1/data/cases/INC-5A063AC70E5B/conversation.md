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
opaque_id: INC-5A063AC70E5B
observation_window={"duration_rel_s":1740.0,"source_metric_rows":30}
selection_summary={"candidate_count":60,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":498,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["adservice","adservice-0","adservice-1","adservice-2","cartservice","cartservice-0","cartservice-1","cartservice-2","checkoutservice","checkoutservice-0","checkoutservice-1","checkoutservice-2","currencyservice","currencyservice-0","currencyservice-1","currencyservice-2","emailservice","emailservice-0","emailservice-1","emailservice-2","example-ant-10-29173920-kh429","example-ant-29173920-v886k","frontend","frontend-0","frontend-1","frontend-2","hipstershop","k8s-master1","k8s-master2","k8s-master3","node-1","node-2","node-3","node-4","node-5","node-6","node-7","node-8","paymentservice","paymentservice-0","paymentservice-1","paymentservice-2","productcatalogservice","productcatalogservice-0","productcatalogservice-1","productcatalogservice-2","recommendationservice","recommendationservice-0","recommendationservice-1","recommendationservice-2","redis","redis-cart","redis-cart-0","shippingservice","shippingservice-0","shippingservice-1","shippingservice-2","tidb-pd","tidb-tidb","tidb-tikv"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[13.594,40.781,67.969,95.156,122.344,149.531,176.719,203.906,231.094,258.281,285.469,312.656,339.844,367.031,394.219,421.406,448.594,475.781,502.969,530.156,557.344,584.531,611.719,638.906,666.094,693.281,720.469,747.656,774.844,802.031,829.219,856.406,883.594,910.781,937.969,965.156,992.344,1019.531,1046.719,1073.906,1101.094,1128.281,1155.469,1182.656,1209.844,1237.031,1264.219,1291.406,1318.594,1345.781,1372.969,1400.156,1427.344,1454.531,1481.719,1508.906,1536.094,1563.281,1590.469,1617.656,1644.844,1672.031,1699.219,1726.406]
[M1] rank=1 service=adservice-0 metric=pod_memory_working_set_bytes baseline=19.337333 peak=7983946.72 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,107.59,-6.51,-101.08,0,0,0,0,81.39,-81.39,0,0,0,0,0,0,0,0,0,117.91,-117.91,0,0,7983946.72,-7983946.72,0,0,0
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M2] rank=2 service=node-7 metric=node_network_receive_bytes_total baseline=164.07 peak=164.04 signed_z=-999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:164.07,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,-0.03,0.03,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M3] rank=3 service=paymentservice-2 metric=pod_memory_working_set_bytes baseline=1206.904 peak=593230.48 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:814.37,-14.01,246.92,-5.72,417.45,138.71,-683.55,253.21,-757.78,1801.05,-1050.18,213.11,-111.98,306.82,-291.03,298.17,101.95,-457.51,596.41,-191.19,-139.58,-519,45.41,912.56,-1502.72,1295.99,-303.37,-268.8,-87.49,592172.26
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M4] rank=4 service=tidb-tidb metric=qps baseline=0.0 peak=1.0 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.535,-0.535,0,0,0,0,0,0,0,0,0,0,0,1,-0.655
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M5] rank=5 service=tidb-tikv metric=raft_apply_wait baseline=0.0 peak=0.01 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.01,-0.01,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M6] rank=6 service=tidb-tikv metric=raft_propose_wait baseline=0.0 peak=0.02 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.02,-0.02,0,0,0,0,0.01,-0.01
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M7] rank=7 service=currencyservice-1 metric=pod_memory_working_set_bytes baseline=3114.204667 peak=710903.49 signed_z=729.277 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:677.28,1840.01,93.9,-126.09,851.76,11.66,-410.89,-523.22,-5.43,1663.1,-946.13,637.74,645.85,226.11,-666.75,-779.72,611.67,-1670.06,1911,-321.07,674659.66,-677735.71,1049.55,2369.89,-1575.37,133.01,-787.27,391.43,618.12,708059.46
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M8] rank=8 service=redis-cart-0 metric=pod_processes baseline=1.0 peak=2.0 signed_z=500.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,-1,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M9] rank=9 service=tidb-tikv metric=write_wal_mbps baseline=13.079333 peak=2885.89 signed_z=258.617 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:20.89,-19.85,24.72,-15.32,0,1.05,0,14.27,-15.32,1.05,-11.49,42.33,-41.29,1.05,9.4,1546.58,-1543.45,32.47,-36.65,0,0,-10.44,25.76,-15.32,1.05,0,-11.49,35.16,2850.73,-2297.09
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M10] rank=10 service=frontend-0 metric=rrt baseline=13184.48 peak=152824.66 signed_z=44.821 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:11975.11,468.46,-167.96,376.22,-753,873.71,-754.25,820.31,-88.2,-416.91,-452.29,881.12,-781.3,428.5,12365.35,93643.54,-15906.55,20674.6,2321.38,-42691.74,43236.39,-56903.96,39348.14,26615.79,-63881.94,81594.14,-103576.47,94385.75,-96109.07,-35833.64
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M11] rank=11 service=frontend-1 metric=rrt baseline=13484.522667 peak=174183.4 signed_z=43.834 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:12279.62,413.17,185.11,-674.05,62.65,661.69,-878.63,431.29,-36.52,749.18,-1733.42,1731.89,-373.5,-539.41,14822.05,96828.9,-24309.85,64887.46,-90537.97,12711.74,41371.56,-66328.29,112458.73,-89590.73,-5346.4,2587.78,66820.01,-66817.91,-15077.25,-53938.8
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M12] rank=12 service=node-5 metric=node_network_transmit_bytes_total baseline=5239.902667 peak=5323.93 signed_z=34.845 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:5239.2,0.6,0.6,1.6,-1.4,1.27,2.86,-7.73,2.87,-4.87,2.27,5.66,-5.26,3.06,-1.26,-0.6,85.06,-86.93,2.73,-2.2,3.47,0.67,-4.07,1.6,-2.6,0.4,0.13,2.34,-2.34,0.54
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[1440.0,1560.0]

=== LOG SUMMARY ===
{"entries":[{"change_pct":-100.0,"n_during":0,"n_pre":30,"service":"redis-cart-0"},{"change_pct":-94.2,"n_during":8,"n_pre":137,"service":"emailservice-1"},{"change_pct":-94.2,"n_during":8,"n_pre":137,"service":"emailservice-2"},{"change_pct":-94.1,"n_during":8,"n_pre":136,"service":"emailservice-0"},{"change_pct":-93.9,"n_during":695,"n_pre":11350,"service":"frontend-0"},{"change_pct":-93.8,"n_during":153,"n_pre":2457,"service":"cartservice-1"},{"change_pct":-93.8,"n_during":1551,"n_pre":25055,"service":"currencyservice-0"},{"change_pct":-93.6,"n_during":390,"n_pre":6065,"service":"adservice-2"}],"mode":"volume","omitted_services":15,"service_count":23}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":94.4,"error_pct":0.0,"p95_during_ms":15076.8035,"p95_pre_ms":7755.2746,"service":"checkoutservice","spans":5105},{"delta_pct":-18.5,"error_pct":0.0,"p95_during_ms":3.6762999999999995,"p95_pre_ms":4.510200000000001,"service":"cartservice","spans":10316},{"delta_pct":-18.1,"error_pct":0.0,"p95_during_ms":2.389999999999997,"p95_pre_ms":2.9185000000000034,"service":"redis","spans":11202},{"delta_pct":-12.1,"error_pct":0.0,"p95_during_ms":0.9516499999999999,"p95_pre_ms":1.08255,"service":"emailservice","spans":434},{"delta_pct":6.9,"error_pct":0.0,"p95_during_ms":0.5103999999999999,"p95_pre_ms":0.4775499999999997,"service":"shippingservice","spans":3020},{"delta_pct":-5.7,"error_pct":0.0,"p95_during_ms":4.549699999999999,"p95_pre_ms":4.82315,"service":"recommendationservice","spans":15490},{"delta_pct":1.1,"error_pct":0.0,"p95_during_ms":14.668000000000001,"p95_pre_ms":14.505,"service":"productcatalogservice","spans":58254},{"delta_pct":0.1,"error_pct":0.0,"p95_during_ms":89.3671999999998,"p95_pre_ms":89.25049999999995,"service":"frontend","spans":126217}],"omitted_services":0,"service_count":8}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=10 omitted_edges=3
[{"evidence_source":"metric","onset_rel_s":900.0,"rank":1,"service":"tidb-tikv","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":900.0,"rank":2,"service":"frontend","severity_z":44.821},{"evidence_source":"metric","onset_rel_s":900.0,"rank":3,"service":"hipstershop","severity_z":18.533},{"evidence_source":"metric","onset_rel_s":900.0,"rank":4,"service":"checkoutservice","severity_z":16.889},{"evidence_source":"metric","onset_rel_s":900.0,"rank":5,"service":"cartservice","severity_z":13.888},{"evidence_source":"metric","onset_rel_s":960.0,"rank":6,"service":"node-5","severity_z":34.845},{"evidence_source":"metric","onset_rel_s":960.0,"rank":7,"service":"node-1","severity_z":22.698},{"evidence_source":"metric","onset_rel_s":1020.0,"rank":8,"service":"node-7","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1020.0,"rank":9,"service":"redis-cart","severity_z":500.0},{"evidence_source":"metric","onset_rel_s":1500.0,"rank":10,"service":"adservice","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1680.0,"rank":11,"service":"tidb-tidb","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1680.0,"rank":12,"service":"shippingservice","severity_z":19.949},{"evidence_source":"metric","onset_rel_s":1740.0,"rank":13,"service":"paymentservice","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1740.0,"rank":14,"service":"currencyservice","severity_z":729.277}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"cartservice","caller":"checkoutservice"},{"callee":"shippingservice","caller":"checkoutservice"},{"callee":"cartservice","caller":"frontend"},{"callee":"checkoutservice","caller":"frontend"},{"callee":"shippingservice","caller":"frontend"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

[excluded before optimizer]

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
opaque_id: INC-0268B73CA997
observation_window={"duration_rel_s":1740.0,"source_metric_rows":30}
selection_summary={"candidate_count":60,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":532,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["adservice","adservice-0","adservice-1","adservice-2","cartservice","cartservice-0","cartservice-1","cartservice-2","checkoutservice","checkoutservice-0","checkoutservice-1","checkoutservice-2","currencyservice","currencyservice-0","currencyservice-1","currencyservice-2","emailservice","emailservice-0","emailservice-1","emailservice-2","example-ant-10-29155200-sh4b9","example-ant-29155200-tblqb","frontend","frontend-0","frontend-1","frontend-2","hipstershop","k8s-master1","k8s-master2","k8s-master3","node-1","node-2","node-3","node-4","node-5","node-6","node-7","node-8","paymentservice","paymentservice-0","paymentservice-1","paymentservice-2","productcatalogservice","productcatalogservice-0","productcatalogservice-1","productcatalogservice-2","recommendationservice","recommendationservice-0","recommendationservice-1","recommendationservice-2","redis","redis-cart","redis-cart-0","shippingservice","shippingservice-0","shippingservice-1","shippingservice-2","tidb-pd","tidb-tidb","tidb-tikv"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[13.594,40.781,67.969,95.156,122.344,149.531,176.719,203.906,231.094,258.281,285.469,312.656,339.844,367.031,394.219,421.406,448.594,475.781,502.969,530.156,557.344,584.531,611.719,638.906,666.094,693.281,720.469,747.656,774.844,802.031,829.219,856.406,883.594,910.781,937.969,965.156,992.344,1019.531,1046.719,1073.906,1101.094,1128.281,1155.469,1182.656,1209.844,1237.031,1264.219,1291.406,1318.594,1345.781,1372.969,1400.156,1427.344,1454.531,1481.719,1508.906,1536.094,1563.281,1590.469,1617.656,1644.844,1672.031,1699.219,1726.406]
[M1] rank=1 service=adservice-2 metric=pod_memory_working_set_bytes baseline=6.233333 peak=8004423.83 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,93.5,-93.5,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,8004423.83,-8004423.83,0,0,0,0,0
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M2] rank=2 service=checkoutservice-2 metric=rrt baseline=6994.156 peak=4976998.73 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:6893.27,1662.91,-1758.36,316.88,-919.41,1571.95,-1205.18,-199.19,2702.23,-2483.27,1367.96,-1428.68,-615.13,977.43,-1127.72,-915.35,0,0,0,0,0,-1833.94,4973992.33,-4970292.77
missing_mask_bits=0101010101101010101011010101010110101010101101111111111111101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,1,0,1
[M3] rank=3 service=checkoutservice-2 metric=rrt_max baseline=194866.533333 peak=843177953.0 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:167311,85163,-109592,103006,-90102,43977,-32646,37121,18902,-56519,50485,8644,-80712,53911,11986,-114905,0,0,0,0,0,-17129,843099052,-843008282
missing_mask_bits=0101010101101010101011010101010110101010101101111111111111101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,1,0,1
[M4] rank=4 service=checkoutservice metric=rrt baseline=6994.156 peak=4976998.73 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:6893.27,1662.91,-1758.36,316.88,-919.41,1571.95,-1205.18,-199.19,2702.23,-2483.27,1367.96,-1428.68,-615.13,977.43,-1127.72,-915.35,0,0,0,0,0,-1833.94,4973992.33,-4970292.77
missing_mask_bits=0101010101101010101011010101010110101010101101111111111111101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,1,0,1
[M5] rank=5 service=checkoutservice metric=rrt_max baseline=194866.533333 peak=843177953.0 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:167311,85163,-109592,103006,-90102,43977,-32646,37121,18902,-56519,50485,8644,-80712,53911,11986,-114905,0,0,0,0,0,-17129,843099052,-843008282
missing_mask_bits=0101010101101010101011010101010110101010101101111111111111101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,1,0,1
[M6] rank=6 service=frontend-0 metric=rrt baseline=12474.915333 peak=2507490.42 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:13467.82,-1206.74,445.81,-1164.94,866.45,-812.65,1612.02,-622.76,513.29,-863.01,-142.91,774.28,-452.69,-1584.41,2983.34,308714.77,210380.95,-520598.22,422598.07,-423655.81,204947.73,144910.9,-199487.49,-149888.66,381589.81,-235785.29,13685.72,-20594.23,2356859.27,-2496341.18
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M7] rank=7 service=frontend-0 metric=rrt_max baseline=233744.6 peak=842285599.0 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:241200,47796,-122968,78289,-55445,89548,-40221,42157,15956,-60088,-76914,138016,-113382,56029,-73281,59835895,27,-59873789,59873011,-59889768,59889679,387,-1298,-59879364,59880619,-1090,589,250,782283759,-842062495
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M8] rank=8 service=frontend-0 metric=server_error baseline=0.0 peak=6.0 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,2,4,-6,4,-4,2,2,-2,-2,4,-2,0,0,0,-2
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M9] rank=9 service=frontend-0 metric=server_error_ratio baseline=0.0 peak=0.87 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.52,0.35,-0.87,0.71,-0.71,0.34,0.25,-0.34,-0.25,0.64,-0.4,0.03,-0.04,0.02,-0.25
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M10] rank=10 service=frontend-1 metric=rrt_max baseline=219119.533333 peak=159213539.0 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:223606,6903,-26584,51116,-62788,71445,-25127,39713,13466,-77953,-85907,82147,-79296,147425,-129641,-2438,59856712,-59876170,59875666,-58,-59882707,59883009,-445,-430,52,-835,-59879459,59880664,329,99211124
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M11] rank=11 service=frontend-1 metric=server_error baseline=0.0 peak=6.0 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,4,-4,6,-4,-2,4,-2,0,2,-2,-2,4,-2,-2
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M12] rank=12 service=frontend-1 metric=server_error_ratio baseline=0.0 peak=0.91 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.34,-0.34,0.91,-0.71,-0.2,0.58,-0.38,0.15,0.31,-0.4,-0.26,0.71,-0.46,-0.25
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[1320.0,1440.0]

=== LOG SUMMARY ===
{"entries":[{"error_logs":16,"error_pct":0.44,"service":"frontend-0","total_logs":3620},{"error_logs":16,"error_pct":0.5,"service":"frontend-1","total_logs":3230},{"error_logs":15,"error_pct":0.51,"service":"frontend-2","total_logs":2962}],"mode":"errors","omitted_services":20,"service_count":23}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":-33.2,"error_pct":0.0,"p95_during_ms":1.7705999999999997,"p95_pre_ms":2.6490999999999976,"service":"redis","spans":3061},{"delta_pct":-24.4,"error_pct":0.0,"p95_during_ms":3.203799999999999,"p95_pre_ms":4.236950000000001,"service":"cartservice","spans":2818},{"delta_pct":-21.8,"error_pct":0.0,"p95_during_ms":0.39880000000000004,"p95_pre_ms":0.5097999999999999,"service":"shippingservice","spans":762},{"delta_pct":-4.7,"error_pct":0.0,"p95_during_ms":13.45525,"p95_pre_ms":14.119149999999998,"service":"productcatalogservice","spans":15976},{"delta_pct":-0.7,"error_pct":0.0,"p95_during_ms":5.09615,"p95_pre_ms":5.133899999999998,"service":"recommendationservice","spans":4246},{"delta_pct":-0.4,"error_pct":0.0,"p95_during_ms":92.4516,"p95_pre_ms":92.8304,"service":"frontend","spans":35114},{"delta_pct":null,"error_pct":0.0,"p95_during_ms":null,"p95_pre_ms":140.82399999999998,"service":"checkoutservice","spans":983},{"delta_pct":null,"error_pct":0.0,"p95_during_ms":null,"p95_pre_ms":1.107,"service":"emailservice","spans":81}],"omitted_services":0,"service_count":8}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=9 omitted_edges=3
[{"evidence_source":"metric","onset_rel_s":900.0,"rank":1,"service":"paymentservice","severity_z":446.446},{"evidence_source":"metric","onset_rel_s":900.0,"rank":2,"service":"recommendationservice","severity_z":12.667},{"evidence_source":"metric","onset_rel_s":900.0,"rank":3,"service":"currencyservice","severity_z":12.463},{"evidence_source":"metric","onset_rel_s":1080.0,"rank":4,"service":"tidb-tikv","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1200.0,"rank":5,"service":"node-3","severity_z":22.042},{"evidence_source":"metric","onset_rel_s":1200.0,"rank":6,"service":"node-1","severity_z":20.441},{"evidence_source":"metric","onset_rel_s":1200.0,"rank":7,"service":"node-6","severity_z":15.36},{"evidence_source":"metric","onset_rel_s":1380.0,"rank":8,"service":"adservice","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1440.0,"rank":9,"service":"tidb-tidb","severity_z":800.0},{"evidence_source":"metric","onset_rel_s":1500.0,"rank":10,"service":"node-8","severity_z":22.726},{"evidence_source":"metric","onset_rel_s":1680.0,"rank":11,"service":"checkoutservice","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1680.0,"rank":12,"service":"frontend","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1680.0,"rank":13,"service":"hipstershop","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1680.0,"rank":14,"service":"shippingservice","severity_z":14.762}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"shippingservice","caller":"checkoutservice"},{"callee":"checkoutservice","caller":"frontend"},{"callee":"recommendationservice","caller":"frontend"},{"callee":"shippingservice","caller":"frontend"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

[excluded before optimizer]

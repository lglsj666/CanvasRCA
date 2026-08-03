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
opaque_id: INC-9ED6E23FA225
observation_window={"duration_rel_s":1740.0,"source_metric_rows":30}
selection_summary={"candidate_count":60,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":488,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["adservice","adservice-0","adservice-1","adservice-2","cartservice","cartservice-0","cartservice-1","cartservice-2","checkoutservice","checkoutservice-0","checkoutservice-1","checkoutservice-2","currencyservice","currencyservice-0","currencyservice-1","currencyservice-2","emailservice","emailservice-0","emailservice-1","emailservice-2","example-ant-10-29182560-4gbdw","example-ant-29182560-r7p69","frontend","frontend-0","frontend-1","frontend-2","hipstershop","k8s-master1","k8s-master2","k8s-master3","node-1","node-2","node-3","node-4","node-5","node-6","node-7","node-8","paymentservice","paymentservice-0","paymentservice-1","paymentservice-2","productcatalogservice","productcatalogservice-0","productcatalogservice-1","productcatalogservice-2","recommendationservice","recommendationservice-0","recommendationservice-1","recommendationservice-2","redis","redis-cart","redis-cart-0","shippingservice","shippingservice-0","shippingservice-1","shippingservice-2","tidb-pd","tidb-tidb","tidb-tikv"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[13.594,40.781,67.969,95.156,122.344,149.531,176.719,203.906,231.094,258.281,285.469,312.656,339.844,367.031,394.219,421.406,448.594,475.781,502.969,530.156,557.344,584.531,611.719,638.906,666.094,693.281,720.469,747.656,774.844,802.031,829.219,856.406,883.594,910.781,937.969,965.156,992.344,1019.531,1046.719,1073.906,1101.094,1128.281,1155.469,1182.656,1209.844,1237.031,1264.219,1291.406,1318.594,1345.781,1372.969,1400.156,1427.344,1454.531,1481.719,1508.906,1536.094,1563.281,1590.469,1617.656,1644.844,1672.031,1699.219,1726.406]
[M1] rank=1 service=adservice-1 metric=pod_memory_working_set_bytes baseline=15.282667 peak=9110895.35 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,150.27,-150.27,0,0,78.97,-78.97,0,0,0,0,0,0,0,0,0,0,94.3,-94.3,0,0,9110895.35,-9110895.35,0
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M2] rank=2 service=currencyservice-0 metric=pod_memory_working_set_bytes baseline=3431.688 peak=1245711.22 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:2221.95,1170.67,-2655.13,2711.24,-773.09,2468.88,-2395.11,2259.46,-1736.52,503.78,-477.87,-392.99,1237.23,136.97,142.64,-2105.33,1243394.44,-598679.33,-644060.6,12.7,-1287.35,844.09,-1105.6,2560.25,-1540.8,1523.96,24.45,-629.14,-44.17,302.41
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M3] rank=3 service=node-2 metric=node_filesystem_usage_rate baseline=29.87 peak=29.875 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:29.87,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.005,0,0,0,0,0,0,0,0,0
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M4] rank=4 service=tidb-tidb metric=qps baseline=0.0 peak=0.535 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.535,-0.535,0,0,0,0,0,0,0,0,0,0.41,-0.41,0,0
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M5] rank=5 service=frontend-0 metric=rrt_max baseline=191143.8 peak=9346092.0 signed_z=166.323 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:111811,142511,-108990,90158,-106210,86747,-49347,72543,-58003,39919,9141,-13001,-93603,163154,-178262,8911763,-8903417,9002128,-228647,147103,-8914222,9094486,-9111842,9240172,-9170418,8913491,-8770528,-91978,322,-115455
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M6] rank=6 service=frontend-0 metric=rrt baseline=11947.262667 peak=128279.53 signed_z=110.191 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:12406.67,-1444.16,1978.23,-1908.51,2135.27,-3198.36,3972.01,-3183.83,1031.24,-635.06,474.76,76.46,1497.01,-1319.42,790.29,92424.87,-92971.74,112523.37,-95709.91,70035.9,-87322.45,110858.63,-111037.16,116805.42,-117147.73,49078.7,-47028.13,-1291.61,967.55,-2013.64
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M7] rank=7 service=frontend-2 metric=rrt baseline=13098.353333 peak=91041.2 signed_z=25.836 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:11487.44,1566.47,-861.89,329.52,-44.21,-280.28,-157.1,1439.42,-925.56,-1092.59,197.23,868.29,-740.68,1058.87,11350.55,26883.21,33933.58,-34835.62,37673.1,-47152.75,38278.16,-29324.75,41390.79,-45893.76,37738.96,-38059.37,-32554.45,-102.92,-120.47,391.74
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M8] rank=8 service=tidb-tikv metric=snapshot_apply_count baseline=0.064 peak=1.04 signed_z=24.523 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.04,0,0,0,0.09,-0.09,0,0,0.09,0,-0.09,0,0,0,0.09,0.91,-1,0.27,-0.18,0.05,-0.14,0,0,0,0.09,-0.09,0.78,-0.78,0.09,0
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M9] rank=9 service=tidb-tikv metric=grpc_qps baseline=0.395667 peak=0.91 signed_z=22.142 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.39,0,-0.025,0.025,0.045,-0.07,0.025,0,0.045,0,-0.045,-0.025,0.025,0,0.025,0.495,-0.52,0.155,-0.09,-0.01,-0.08,0.025,0,-0.025,0.07,-0.045,0.41,-0.41,0.065,-0.04
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M10] rank=10 service=currencyservice-2 metric=rrt_max baseline=69816.666667 peak=5065513.0 signed_z=20.019 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:2037,1143,945,-2260,1339,459,-1658,7095,-5987,-1070,-261,1878,-1856,368,1001325,67850,4880,-9948,15384,-19198,-27583,43188,4381,-10804,-10811,4004677,-5062073,-687,704,-1918
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M11] rank=11 service=frontend metric=rrt baseline=13105.471333 peak=77602.48 signed_z=19.882 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:11532.6,1195.8,-338.87,-106.15,29.33,-170.34,16.57,1029.49,-740.25,-881.45,238.43,406.65,-133.78,511.87,12556,38889.7,9795.59,-12808.58,10363.94,-19708.63,20646.06,-15745.98,21024.48,-23576.08,23375,-33603.96,-31553.44,-4.17,-190.96,152.21
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M12] rank=12 service=currencyservice metric=rrt_max baseline=103188.266667 peak=5065513.0 signed_z=18.849 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:5635,8946,2437,-1065,-4149,1353,2217,179439,-184322,19447,-17867,10252,76667,-84967,1057630,2516,2058,-9948,15384,-3719,3128,-3002,4381,1,-4705,3987766,-5026733,-28141,86676,-89628
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[1140.0,1740.0]

=== LOG SUMMARY ===
{"entries":[{"change_pct":-52.9,"n_during":8,"n_pre":17,"service":"redis-cart-0"},{"change_pct":-52.3,"n_during":6625,"n_pre":13883,"service":"frontend-2"},{"change_pct":-52.3,"n_during":776,"n_pre":1628,"service":"shippingservice-2"},{"change_pct":-52.2,"n_during":1308,"n_pre":2734,"service":"adservice-0"},{"change_pct":-52.2,"n_during":280,"n_pre":586,"service":"currencyservice-2"},{"change_pct":-52.2,"n_during":1068,"n_pre":2232,"service":"shippingservice-0"},{"change_pct":-52.1,"n_during":27774,"n_pre":57969,"service":"cartservice-1"},{"change_pct":-52.0,"n_during":2622,"n_pre":5461,"service":"recommendationservice-2"}],"mode":"volume","omitted_services":15,"service_count":23}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":105.1,"error_pct":0.0,"p95_during_ms":6100.521,"p95_pre_ms":2974.5620499999995,"service":"checkoutservice","spans":5276},{"delta_pct":-13.7,"error_pct":0.0,"p95_during_ms":2.6310000000000002,"p95_pre_ms":3.049249999999997,"service":"redis","spans":11660},{"delta_pct":-9.5,"error_pct":0.0,"p95_during_ms":4.131199999999996,"p95_pre_ms":4.564,"service":"cartservice","spans":10756},{"delta_pct":-8.6,"error_pct":0.0,"p95_during_ms":0.428,"p95_pre_ms":0.46819999999999984,"service":"shippingservice","spans":3147},{"delta_pct":-2.5,"error_pct":0.0,"p95_during_ms":13.33155,"p95_pre_ms":13.677,"service":"productcatalogservice","spans":60684},{"delta_pct":-2.0,"error_pct":0.0,"p95_during_ms":1.0090999999999999,"p95_pre_ms":1.0298,"service":"emailservice","spans":450},{"delta_pct":-1.6,"error_pct":0.0,"p95_during_ms":87.5882,"p95_pre_ms":88.99240000000005,"service":"frontend","spans":131393},{"delta_pct":0.5,"error_pct":0.0,"p95_during_ms":5.570500000000002,"p95_pre_ms":5.5448999999999975,"service":"recommendationservice","spans":16112}],"omitted_services":0,"service_count":8}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=7 omitted_edges=0
[{"evidence_source":"metric","onset_rel_s":900.0,"rank":1,"service":"tidb-tidb","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":900.0,"rank":2,"service":"tidb-tikv","severity_z":24.523},{"evidence_source":"metric","onset_rel_s":900.0,"rank":3,"service":"hipstershop","severity_z":18.397},{"evidence_source":"metric","onset_rel_s":900.0,"rank":4,"service":"checkoutservice","severity_z":12.831},{"evidence_source":"metric","onset_rel_s":960.0,"rank":5,"service":"currencyservice","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1020.0,"rank":6,"service":"frontend","severity_z":166.323},{"evidence_source":"metric","onset_rel_s":1200.0,"rank":7,"service":"node-2","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1260.0,"rank":8,"service":"node-6","severity_z":10.612},{"evidence_source":"metric","onset_rel_s":1620.0,"rank":9,"service":"adservice","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1680.0,"rank":10,"service":"cartservice","severity_z":14.836},{"evidence_source":"none","onset_rel_s":null,"rank":11,"service":"paymentservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":12,"service":"redis-cart","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":13,"service":"recommendationservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":14,"service":"emailservice","severity_z":0.0}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"cartservice","caller":"checkoutservice"},{"callee":"emailservice","caller":"checkoutservice"},{"callee":"cartservice","caller":"frontend"},{"callee":"checkoutservice","caller":"frontend"},{"callee":"recommendationservice","caller":"frontend"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

[excluded before optimizer]

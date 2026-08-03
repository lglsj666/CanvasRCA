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
opaque_id: INC-64B26A296FC6
observation_window={"duration_rel_s":1920.0,"source_metric_rows":33}
selection_summary={"candidate_count":60,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":492,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["adservice","adservice-0","adservice-1","adservice-2","cartservice","cartservice-0","cartservice-1","cartservice-2","checkoutservice","checkoutservice-0","checkoutservice-1","checkoutservice-2","currencyservice","currencyservice-0","currencyservice-1","currencyservice-2","emailservice","emailservice-0","emailservice-1","emailservice-2","example-ant-10-29162400-r2drh","example-ant-29162400-cdnr4","frontend","frontend-0","frontend-1","frontend-2","hipstershop","k8s-master1","k8s-master2","k8s-master3","node-1","node-2","node-3","node-4","node-5","node-6","node-7","node-8","paymentservice","paymentservice-0","paymentservice-1","paymentservice-2","productcatalogservice","productcatalogservice-0","productcatalogservice-1","productcatalogservice-2","recommendationservice","recommendationservice-0","recommendationservice-1","recommendationservice-2","redis","redis-cart","redis-cart-0","shippingservice","shippingservice-0","shippingservice-1","shippingservice-2","tidb-pd","tidb-tidb","tidb-tikv"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[15.0,45.0,75.0,105.0,135.0,165.0,195.0,225.0,255.0,285.0,315.0,345.0,375.0,405.0,435.0,465.0,495.0,525.0,555.0,585.0,615.0,645.0,675.0,705.0,735.0,765.0,795.0,825.0,855.0,885.0,915.0,945.0,975.0,1005.0,1035.0,1065.0,1095.0,1125.0,1155.0,1185.0,1215.0,1245.0,1275.0,1305.0,1335.0,1365.0,1395.0,1425.0,1455.0,1485.0,1515.0,1545.0,1575.0,1605.0,1635.0,1665.0,1695.0,1725.0,1755.0,1785.0,1815.0,1845.0,1875.0,1905.0]
[M1] rank=1 service=adservice-2 metric=pod_memory_working_set_bytes baseline=10.103125 peak=19916804.88 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,161.65,-161.65,0,0,0,0,0,0,19916804.88,-19916804.88,0,89.53,-89.53,0,0,715.82,-715.82,0,0,0,0,0
missing_mask_bits=0101010101010101010101010101010101010101010101010101010101010100
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1
[M2] rank=2 service=tidb-tidb metric=duration_99th baseline=0.01 peak=0.03 signed_z=666.667 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.01,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.02,-0.02,0,0,0,0,0,0,0
missing_mask_bits=0101010101010101010101010101010101010101010101010101010101010100
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1
[M3] rank=3 service=tidb-tikv metric=read_mbps baseline=38777.425625 peak=6979394.51 signed_z=81.777 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:13685.56,-46.92,1355.94,-702.31,472.15,10722.07,-10291.8,-948.58,400.6,318.36,22303.29,-21408.92,-841.17,-1097.76,1847.91,350920.85,-350691.27,-524.51,-1141.91,-231.22,10874.04,-10685.93,668.11,529.46,-1058.28,6964966.75,-6963728.8,-1668.82,413.11,199.6,10814.71,-10799.4,485.31
missing_mask_bits=0101010101010101010101010101010101010101010101010101010101010100
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1
[M4] rank=4 service=tidb-tidb metric=memory_usage baseline=1046224896.0 peak=1021517824.0 signed_z=-77.83 onset_bin=62 onset_rel_s=1875.0 persistence_bins=2
values_compact=delta:1046224896,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,-24707072,0,0,0,0,0,0,0
missing_mask_bits=0101010101010101010101010101010101010101010101010101010101010100
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1
[M5] rank=5 service=redis-cart-0 metric=pod_cpu_usage baseline=0.000625 peak=0.13 signed_z=53.447 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0.01,-0.01,0,0,0,0,0.13,-0.13,0,0,0,0,0,0,0,0,0,0,0,0.13,-0.13,0,0
missing_mask_bits=0101010101010101010101010101010101010101010101010101010101010100
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1
[M6] rank=6 service=redis-cart-0 metric=pod_fs_writes_bytes baseline=6844.268125 peak=1223257.12 signed_z=45.889 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,109508.29,-109508.29,0,0,0,0,934351.53,-934351.53,0,0,0,0,0,0,0,0,0,0,0,1223257.12,-1223257.12,0,0
missing_mask_bits=0101010101010101010101010101010101010101010101010101010101010100
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1
[M7] rank=7 service=tidb-tikv metric=snapshot_apply_count baseline=0.105 peak=5.33 signed_z=45.285 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.22,-0.18,0,0,0,0.09,-0.09,0,0,0.09,0.27,-0.36,0,0,0,0.32,-0.32,0,0,0,0.18,-0.18,0,0,5.29,-5.15,-0.14,0,0,0,0.18,-0.18,0
missing_mask_bits=0101010101010101010101010101010101010101010101010101010101010100
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1
[M8] rank=8 service=cartservice-1 metric=rrt baseline=1596.734375 peak=11445.9 signed_z=43.222 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:1570.94,-98.27,-54.96,669.91,-522.41,-165.87,110.62,-65.93,467.1,-416.22,-134.87,412.3,-190.53,491.86,-633.56,6.15,920.63,-876.33,212.39,172.37,-262.99,-6.33,9839.9,-9785.04,-286.15,410.14,-215.98,-40.55,24.93,-8.21,-22.71,312.3,-456.13
missing_mask_bits=0101010101010101010101010101010101010101010101010101010101010100
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1
[M9] rank=9 service=currencyservice-0 metric=rrt_max baseline=3968.8125 peak=61565.0 signed_z=38.876 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:3917,-1508,631,-621,851,3508,909,-4312,1244,-1950,468,-423,2584,-915,26,-1032,6905,51283,-57503,-756,1298,-38,-2432,169,401,1800,-1975,757,1268,664,64,-996,1821
missing_mask_bits=0101010101010101010101010101010101010101010101010101010101010100
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1
[M10] rank=10 service=tidb-tikv metric=grpc_qps baseline=0.417813 peak=3.01 signed_z=37.799 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.475,-0.085,0,-0.025,0.025,0.045,-0.07,0.025,0,0,0.21,-0.21,-0.025,0.025,0,0.18,-0.18,0,-0.025,0.025,0.11,-0.135,0.025,0,2.62,-2.545,-0.075,-0.025,0.025,0,0.085,-0.085,0
missing_mask_bits=0101010101010101010101010101010101010101010101010101010101010100
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1
[M11] rank=11 service=cartservice-1 metric=rrt_max baseline=4174.6875 peak=75912.0 signed_z=34.454 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:5017,-2085,-167,6073,-4803,-1593,1160,-861,4226,-4064,-234,3243,-3307,5554,-5541,-28,6454,-5789,738,385,-419,-1127,73080,-72475,-742,186,429,-524,-249,438,26,2396,-2728
missing_mask_bits=0101010101010101010101010101010101010101010101010101010101010100
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1
[M12] rank=12 service=k8s-master1 metric=node_filesystem_free_bytes baseline=4910638336.0 peak=4907638784.0 signed_z=-32.661 onset_bin=62 onset_rel_s=1875.0 persistence_bins=2
values_compact=delta:4910714880,-122880,0,323584,-282624,-57344,0,0,0,-20480,196608,-90112,20480,-110592,98304,-98304,20480,-221184,0,0,-110592,20480,110592,-241664,-16384,204800,-143360,0,192512,0,1355776,-4018176,-86016
missing_mask_bits=0101010101010101010101010101010101010101010101010101010101010100
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[1080.0,1200.0]

=== LOG SUMMARY ===
{"entries":[{"change_pct":-100.0,"n_during":0,"n_pre":25,"service":"redis-cart-0"},{"change_pct":-93.7,"n_during":235,"n_pre":3735,"service":"frontend-2"},{"change_pct":-93.4,"n_during":545,"n_pre":8231,"service":"currencyservice-0"},{"change_pct":-93.3,"n_during":192,"n_pre":2883,"service":"recommendationservice-2"},{"change_pct":-93.2,"n_during":164,"n_pre":2401,"service":"adservice-1"},{"change_pct":-93.2,"n_during":2232,"n_pre":32616,"service":"cartservice-2"},{"change_pct":-93.1,"n_during":124,"n_pre":1808,"service":"shippingservice-0"},{"change_pct":-93.0,"n_during":4,"n_pre":57,"service":"emailservice-1"}],"mode":"volume","omitted_services":15,"service_count":23}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":-29.9,"error_pct":0.0,"p95_during_ms":0.8397999999999999,"p95_pre_ms":1.1974999999999996,"service":"emailservice","spans":172},{"delta_pct":20.1,"error_pct":0.0,"p95_during_ms":0.5476,"p95_pre_ms":0.456,"service":"shippingservice","spans":1195},{"delta_pct":5.6,"error_pct":0.0,"p95_during_ms":4.2673999999999985,"p95_pre_ms":4.04075,"service":"cartservice","spans":4101},{"delta_pct":-4.3,"error_pct":0.0,"p95_during_ms":2.3225,"p95_pre_ms":2.426199999999999,"service":"redis","spans":4442},{"delta_pct":2.8,"error_pct":0.0,"p95_during_ms":145.05714999999992,"p95_pre_ms":141.06349999999998,"service":"checkoutservice","spans":2026},{"delta_pct":2.7,"error_pct":0.0,"p95_during_ms":14.347599999999996,"p95_pre_ms":13.964949999999993,"service":"productcatalogservice","spans":23137},{"delta_pct":1.1,"error_pct":0.0,"p95_during_ms":88.24699999999996,"p95_pre_ms":87.2818,"service":"frontend","spans":50070},{"delta_pct":-1.0,"error_pct":0.0,"p95_during_ms":4.91695,"p95_pre_ms":4.968,"service":"recommendationservice","spans":6150}],"omitted_services":0,"service_count":8}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=8 omitted_edges=1
[{"evidence_source":"metric","onset_rel_s":960.0,"rank":1,"service":"redis-cart","severity_z":53.447},{"evidence_source":"metric","onset_rel_s":1020.0,"rank":2,"service":"currencyservice","severity_z":38.876},{"evidence_source":"metric","onset_rel_s":1140.0,"rank":3,"service":"adservice","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1200.0,"rank":4,"service":"node-4","severity_z":16.781},{"evidence_source":"trace","onset_rel_s":1339.8,"rank":5,"service":"redis","severity_z":64.406},{"evidence_source":"trace","onset_rel_s":1339.8,"rank":6,"service":"cartservice","severity_z":38.37},{"evidence_source":"metric","onset_rel_s":1440.0,"rank":7,"service":"tidb-tidb","severity_z":666.667},{"evidence_source":"metric","onset_rel_s":1440.0,"rank":8,"service":"node-7","severity_z":10.056},{"evidence_source":"metric","onset_rel_s":1500.0,"rank":9,"service":"tidb-tikv","severity_z":81.777},{"evidence_source":"metric","onset_rel_s":1800.0,"rank":10,"service":"k8s-master2","severity_z":13.74},{"evidence_source":"metric","onset_rel_s":1860.0,"rank":11,"service":"k8s-master1","severity_z":32.661},{"evidence_source":"none","onset_rel_s":null,"rank":12,"service":"k8s-master3","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":13,"service":"emailservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":14,"service":"paymentservice","severity_z":0.0}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"redis","caller":"cartservice"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

{"confidence":"medium","reason":"Rank emailservice first because emailservice has direct trace evidence; redis-cart is second despite propagation rank 1 because onset ordering alone does not establish the causal origin. The remaining entries preserve evidence-supported alternatives so the ranking retains calibrated uncertainty instead of collapsing to one answer.","services":["emailservice","redis-cart","currencyservice","adservice","cartservice"]}

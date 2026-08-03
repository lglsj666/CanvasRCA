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
opaque_id: INC-E2C331465308
observation_window={"duration_rel_s":1740.0,"source_metric_rows":30}
selection_summary={"candidate_count":60,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":450,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["adservice","adservice-0","adservice-1","adservice-2","cartservice","cartservice-0","cartservice-1","cartservice-2","checkoutservice","checkoutservice-0","checkoutservice-1","checkoutservice-2","currencyservice","currencyservice-0","currencyservice-1","currencyservice-2","emailservice","emailservice-0","emailservice-1","emailservice-2","example-ant-10-29184000-wx4rn","example-ant-29184000-cgbbl","frontend","frontend-0","frontend-1","frontend-2","hipstershop","k8s-master1","k8s-master2","k8s-master3","node-1","node-2","node-3","node-4","node-5","node-6","node-7","node-8","paymentservice","paymentservice-0","paymentservice-1","paymentservice-2","productcatalogservice","productcatalogservice-0","productcatalogservice-1","productcatalogservice-2","recommendationservice","recommendationservice-0","recommendationservice-1","recommendationservice-2","redis","redis-cart","redis-cart-0","shippingservice","shippingservice-0","shippingservice-1","shippingservice-2","tidb-pd","tidb-tidb","tidb-tikv"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[13.594,40.781,67.969,95.156,122.344,149.531,176.719,203.906,231.094,258.281,285.469,312.656,339.844,367.031,394.219,421.406,448.594,475.781,502.969,530.156,557.344,584.531,611.719,638.906,666.094,693.281,720.469,747.656,774.844,802.031,829.219,856.406,883.594,910.781,937.969,965.156,992.344,1019.531,1046.719,1073.906,1101.094,1128.281,1155.469,1182.656,1209.844,1237.031,1264.219,1291.406,1318.594,1345.781,1372.969,1400.156,1427.344,1454.531,1481.719,1508.906,1536.094,1563.281,1590.469,1617.656,1644.844,1672.031,1699.219,1726.406]
[M1] rank=1 service=adservice-0 metric=pod_memory_working_set_bytes baseline=32.587333 peak=8289810.93 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,277.06,-277.06,0,0,82.85,-82.85,128.9,-128.9,0,0,0,90.62,-90.62,0,0,0,0,0,0,0,8289810.93,-8289810.93,0,0
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M2] rank=2 service=currencyservice-2 metric=pod_memory_working_set_bytes baseline=1911.500667 peak=992768.51 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:1656.58,-3.25,-743.14,768.65,-407.95,1121.35,-454.72,-473.36,842.35,549.09,-583.49,461.46,-1351.89,1423.29,-1450.65,1799.62,-1600.23,1535.02,-2373.6,4122.38,-4262.48,3382.46,-2613.8,614698.08,-615793.98,7448.71,-7403.52,112.74,992362.79,-992040.72
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M3] rank=3 service=tidb-tidb metric=duration_avg baseline=0.0 peak=0.02 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.02,0,-0.02,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M4] rank=4 service=tidb-tidb metric=qps baseline=0.0 peak=0.235 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.235,-0.235,0,0,0,0.165,-0.165,0,0,0,0,0,0,0,0
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M5] rank=5 service=tidb-tikv metric=raft_apply_wait baseline=0.0 peak=0.02 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.02,-0.02,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M6] rank=6 service=tidb-tidb metric=duration_99th baseline=0.01 peak=2.22 signed_z=995.495 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.01,0,0,0,0,0,0,0,0,0,0,0,0,0,0,2.21,-2.21,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M7] rank=7 service=tidb-tidb metric=block_cache_size baseline=14893856.0 peak=2394800.0 signed_z=-839.209 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:14893856,0,0,0,0,0,0,0,0,0,0,0,0,0,0,-12499056,263552,0,0,197664,0,0,0,0,32944,0,0,0,0,0
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M8] rank=8 service=tidb-tikv metric=memory_usage baseline=2041570645.333333 peak=1961447424.0 signed_z=-135.596 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:2041966592,77824,-397312,131072,987136,-589824,-1462272,1474560,-724992,-200704,-409600,286720,651264,-1134592,462848,-79671296,2007040,131072,532480,540672,618496,1052672,466944,-708608,516096,1642496,131072,-61440,-380928,1146880
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M9] rank=9 service=tidb-tikv metric=region_pending baseline=53864.0 peak=818.0 signed_z=-64.344 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:52270,709,126,141,132,139,135,131,153,131,131,130,704,130,145,-54489,132,128,150,142,134,140,706,132,142,129,126,127,154,137
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M10] rank=10 service=node-1 metric=node_disk_written_bytes_total baseline=47907.272 peak=1689907.2 signed_z=51.166 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:78916.27,-77550.94,1365.34,107315.2,-107315.2,-1911.47,63044.27,-12629.34,-4027.73,8226.13,-5222.4,-7953.06,16793.6,12083.2,10478.93,-30822.4,-1877.33,47172.26,27545.6,-22323.2,-89429.33,708232.53,969796.27,-1683148.8,785.07,85640.53,-72635.73,-12800,93354.66,-136.53
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M11] rank=11 service=tidb-pd metric=memory_usage baseline=193699840.0 peak=194355200.0 signed_z=23.314 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:193699840,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,180224,0,0,0,0,241664,0,0,0,0,233472,0,0,0
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M12] rank=12 service=tidb-tikv metric=cpu_usage baseline=0.084667 peak=0.33 signed_z=21.39 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.09,0,0,0,-0.02,0.02,0,-0.02,0,0.02,-0.02,0.02,0.02,-0.02,-0.02,0.26,-0.26,0,0.02,0,0,0,0,-0.02,0.02,0,-0.02,0.02,0,-0.02
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[840.0,1020.0]

=== LOG SUMMARY ===
{"entries":[{"change_pct":-89.7,"n_during":341,"n_pre":3307,"service":"frontend-2"},{"change_pct":-89.5,"n_during":67,"n_pre":639,"service":"adservice-0"},{"change_pct":-89.5,"n_during":263,"n_pre":2507,"service":"recommendationservice-2"},{"change_pct":-89.4,"n_during":155,"n_pre":1463,"service":"adservice-2"},{"change_pct":-89.2,"n_during":1872,"n_pre":17343,"service":"cartservice-1"},{"change_pct":-89.2,"n_during":66,"n_pre":612,"service":"shippingservice-0"},{"change_pct":-88.8,"n_during":1323,"n_pre":11817,"service":"cartservice-2"},{"change_pct":-88.7,"n_during":478,"n_pre":4216,"service":"frontend-0"}],"mode":"volume","omitted_services":15,"service_count":23}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":34.2,"error_pct":0.0,"p95_during_ms":3.97825,"p95_pre_ms":2.964999999999999,"service":"redis","spans":3873},{"delta_pct":15.7,"error_pct":0.0,"p95_during_ms":5.157899999999995,"p95_pre_ms":4.458049999999998,"service":"cartservice","spans":3579},{"delta_pct":5.2,"error_pct":0.0,"p95_during_ms":0.5352,"p95_pre_ms":0.5087999999999997,"service":"shippingservice","spans":1046},{"delta_pct":-4.9,"error_pct":0.0,"p95_during_ms":124.37119999999989,"p95_pre_ms":130.79189999999986,"service":"checkoutservice","spans":1786},{"delta_pct":-3.2,"error_pct":0.0,"p95_during_ms":14.001199999999992,"p95_pre_ms":14.463,"service":"productcatalogservice","spans":20169},{"delta_pct":-2.6,"error_pct":0.0,"p95_during_ms":5.27675,"p95_pre_ms":5.41875,"service":"recommendationservice","spans":5362},{"delta_pct":-1.9,"error_pct":0.0,"p95_during_ms":0.9594999999999998,"p95_pre_ms":0.9779499999999994,"service":"emailservice","spans":152},{"delta_pct":0.5,"error_pct":0.0,"p95_during_ms":93.19979999999998,"p95_pre_ms":92.75979999999997,"service":"frontend","spans":43727}],"omitted_services":0,"service_count":8}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=9 omitted_edges=0
[{"evidence_source":"metric","onset_rel_s":900.0,"rank":1,"service":"tidb-tidb","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":900.0,"rank":2,"service":"tidb-tikv","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":900.0,"rank":3,"service":"k8s-master2","severity_z":18.218},{"evidence_source":"metric","onset_rel_s":1200.0,"rank":4,"service":"node-2","severity_z":17.284},{"evidence_source":"metric","onset_rel_s":1260.0,"rank":5,"service":"tidb-pd","severity_z":23.314},{"evidence_source":"metric","onset_rel_s":1260.0,"rank":6,"service":"shippingservice","severity_z":11.92},{"evidence_source":"metric","onset_rel_s":1320.0,"rank":7,"service":"node-1","severity_z":51.166},{"evidence_source":"metric","onset_rel_s":1440.0,"rank":8,"service":"node-8","severity_z":10.913},{"evidence_source":"metric","onset_rel_s":1560.0,"rank":9,"service":"adservice","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1680.0,"rank":10,"service":"currencyservice","severity_z":999.0},{"evidence_source":"trace","onset_rel_s":1722.0,"rank":11,"service":"cartservice","severity_z":4.544},{"evidence_source":"none","onset_rel_s":null,"rank":12,"service":"emailservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":13,"service":"paymentservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":14,"service":"example-ant","severity_z":0.0}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

{"confidence":"medium","reason":"Rank tidb-tikv first because tidb-tikv has direct raft_apply_wait evidence (signed-z 999, persistence 0 bins); tidb-tidb is second despite propagation rank 1 because onset ordering alone does not establish the causal origin. The remaining entries preserve evidence-supported alternatives so the ranking retains calibrated uncertainty instead of collapsing to one answer.","services":["tidb-tikv","tidb-tidb","tidb-pd","k8s-master2","node-2"]}

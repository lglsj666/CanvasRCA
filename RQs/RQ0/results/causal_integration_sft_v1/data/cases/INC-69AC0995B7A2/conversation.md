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
opaque_id: INC-69AC0995B7A2
observation_window={"duration_rel_s":1800.0,"source_metric_rows":31}
selection_summary={"candidate_count":61,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":557,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["adservice","adservice-0","adservice-1","adservice-2","cartservice","cartservice-0","cartservice-1","cartservice-2","checkoutservice","checkoutservice-0","checkoutservice-1","checkoutservice-2","currencyservice","currencyservice-0","currencyservice-1","currencyservice-2","emailservice","emailservice-0","emailservice-1","emailservice-2","example-ant-10-29159520-nlwlw","example-ant-10-29160960-4hv7k","example-ant-29160960-lpx4l","frontend","frontend-0","frontend-1","frontend-2","hipstershop","k8s-master1","k8s-master2","k8s-master3","node-1","node-2","node-3","node-4","node-5","node-6","node-7","node-8","paymentservice","paymentservice-0","paymentservice-1","paymentservice-2","productcatalogservice","productcatalogservice-0","productcatalogservice-1","productcatalogservice-2","recommendationservice","recommendationservice-0","recommendationservice-1","recommendationservice-2","redis","redis-cart","redis-cart-0","shippingservice","shippingservice-0","shippingservice-1","shippingservice-2","tidb-pd","tidb-tidb","tidb-tikv"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[14.062,42.188,70.312,98.438,126.562,154.688,182.812,210.938,239.062,267.188,295.312,323.438,351.562,379.688,407.812,435.938,464.062,492.188,520.312,548.438,576.562,604.688,632.812,660.938,689.062,717.188,745.312,773.438,801.562,829.688,857.812,885.938,914.062,942.188,970.312,998.438,1026.562,1054.688,1082.812,1110.938,1139.062,1167.188,1195.312,1223.438,1251.562,1279.688,1307.812,1335.938,1364.062,1392.188,1420.312,1448.438,1476.562,1504.688,1532.812,1560.938,1589.062,1617.188,1645.312,1673.438,1701.562,1729.688,1757.812,1785.938]
[M1] rank=1 service=adservice-1 metric=pod_memory_working_set_bytes baseline=5.342667 peak=12564228.7 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,80.14,-80.14,0,0,0,0,0,0,0,12564228.7,-12564228.7,106.47,-106.47,0,4810.95,-4810.95,0,84.64,-84.64,0,0,0
missing_mask_bits=0101010101010101101010101010101101010101010101011010101010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1
[M2] rank=2 service=frontend-0 metric=rrt baseline=11709.096667 peak=12857728.89 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:10346.71,2869.88,-1893.29,1589.87,-2097.04,1409.05,399.47,-932.7,-104.26,374.15,-745.87,730.77,25.34,-344.59,-1460.53,12624148.15,-2631359.61,-2499577.02,2934933.67,-8446151.33,5838380.61,742139.36,-386560.4,4671608.5,-5795766.39,2414569.74,-472476.17,486161.38,-6919724,6919097.22,-9476693.28
missing_mask_bits=0101010101010101101010101010101101010101010101011010101010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1
[M3] rank=3 service=frontend-0 metric=server_error baseline=0.0 peak=12.0 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,8,-2,0,2,-2,0,0,0,0,-2,2,0,0,2,4,-12
missing_mask_bits=0101010101010101101010101010101101010101010101011010101010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1
[M4] rank=4 service=frontend-0 metric=server_error_ratio baseline=0.0 peak=23.08 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,21.05,-4.38,-4.17,4.89,-14.08,9.73,1.25,-0.65,7.79,-9.67,4.03,-0.79,0.79,-11.51,18.8,-23.08
missing_mask_bits=0101010101010101101010101010101101010101010101011010101010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1
[M5] rank=5 service=frontend-1 metric=rrt baseline=14452.582 peak=12858152.07 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:11575.18,995.66,-1170.88,762.63,-1903.71,1667.75,-41.51,-152.72,368.22,-717.36,667.73,-23.03,194.21,-538.47,40124.73,6875622.67,-4343529.02,8006561.07,-3919566.54,5336750.92,-2529473.06,3379977.6,-6538418.94,3157593.95,-7404000.51,6930140.31,-395.53,472127.97,-2804330.39,4759448.55,-9119941.95
missing_mask_bits=0101010101010101101010101010101101010101010101011010101010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1
[M6] rank=6 service=frontend-1 metric=rrt_max baseline=285926.866667 peak=958259279.0 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:242124,-26872,24652,-22743,-50771,71801,-111762,142159,605,-13028,-29844,37449,20629,-15274,736766,58995905,-502,1249,-1223,-824,2083,-2596,1123,32,637,741,-988,229,-615,170,898257967
missing_mask_bits=0101010101010101101010101010101101010101010101011010101010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1
[M7] rank=7 service=frontend-1 metric=server_error baseline=0.0 peak=8.0 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,6,2,-2,0,2,-2,0,-2,2,0,0,0,0,0,2,-8
missing_mask_bits=0101010101010101101010101010101101010101010101011010101010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1
[M8] rank=8 service=frontend-1 metric=server_error_ratio baseline=0.0 peak=21.43 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,11.54,-7.24,13.35,-6.54,8.89,-4.21,5.64,-10.9,5.26,-12.34,11.55,0,0.79,-4.68,7.94,-19.05
missing_mask_bits=0101010101010101101010101010101101010101010101011010101010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1
[M9] rank=9 service=frontend-2 metric=rrt baseline=11720.192667 peak=13343389.22 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:12255.04,178.09,-1306.62,1321.09,-2015.96,3461.98,-3378.6,2501.75,-2192.44,1298.19,-805.46,967.79,-708.32,376.69,-2348.17,9998940.48,-2505638.38,2934924.13,820942.19,-3429254.27,-4934607.83,108642.71,10339835.14,-4767793.43,2015253.36,-8769348.76,2011762.27,8801395.97,-10538632.47,6485308.24,-5293272.07
missing_mask_bits=0101010101010101101010101010101101010101010101011010101010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1
[M10] rank=10 service=frontend-2 metric=rrt_max baseline=209864.0 peak=958890914.0 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:213057,23715,-101741,98737,47000,3519,-177791,174691,-170509,131295,-120705,130929,-16966,-68942,82669,59753066,1333,-1565,-626,2547,-2233,424,334,-734,-848,-406,302,543,2938,-2215,898889096
missing_mask_bits=0101010101010101101010101010101101010101010101011010101010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1
[M11] rank=11 service=frontend-2 metric=server_error baseline=0.0 peak=8.0 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,6,0,2,-2,0,2,-6,6,-2,0,-2,2,2,-2,0,-6
missing_mask_bits=0101010101010101101010101010101101010101010101011010101010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1
[M12] rank=12 service=frontend-2 metric=server_error_ratio baseline=0.0 peak=22.22 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,16.67,-4.17,4.89,1.36,-5.71,-8.22,0.18,17.22,-7.93,3.36,-14.62,3.35,14.67,-17.56,10.8,-14.29
missing_mask_bits=0101010101010101101010101010101101010101010101011010101010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[840.0,1800.0]

=== LOG SUMMARY ===
{"entries":[{"error_logs":50,"error_pct":2.26,"service":"frontend-0","total_logs":2213},{"error_logs":47,"error_pct":2.07,"service":"frontend-1","total_logs":2276},{"error_logs":46,"error_pct":2.06,"service":"frontend-2","total_logs":2238}],"mode":"errors","omitted_services":21,"service_count":24}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":67230.6,"error_pct":0.0,"p95_during_ms":60000.2868,"p95_pre_ms":89.113,"service":"frontend","spans":22898},{"delta_pct":46.1,"error_pct":0.0,"p95_during_ms":7.1000499999999995,"p95_pre_ms":4.85955,"service":"recommendationservice","spans":2754},{"delta_pct":-24.7,"error_pct":0.0,"p95_during_ms":1.8091999999999993,"p95_pre_ms":2.403099999999999,"service":"redis","spans":2144},{"delta_pct":-15.6,"error_pct":0.0,"p95_during_ms":121.04639999999988,"p95_pre_ms":143.44174999999987,"service":"checkoutservice","spans":948},{"delta_pct":-11.7,"error_pct":0.0,"p95_during_ms":3.481149999999998,"p95_pre_ms":3.944,"service":"cartservice","spans":1974},{"delta_pct":-4.6,"error_pct":0.0,"p95_during_ms":0.836,"p95_pre_ms":0.8763500000000001,"service":"emailservice","spans":81},{"delta_pct":-4.0,"error_pct":0.0,"p95_during_ms":0.38124999999999964,"p95_pre_ms":0.397,"service":"shippingservice","spans":536},{"delta_pct":0.7,"error_pct":0.0,"p95_during_ms":13.5575,"p95_pre_ms":13.459399999999988,"service":"productcatalogservice","spans":10289}],"omitted_services":0,"service_count":8}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=5 omitted_edges=1
[{"evidence_source":"trace","onset_rel_s":881.4,"rank":1,"service":"frontend","severity_z":999.0},{"evidence_source":"trace","onset_rel_s":881.4,"rank":2,"service":"recommendationservice","severity_z":13.938},{"evidence_source":"metric","onset_rel_s":900.0,"rank":3,"service":"hipstershop","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":900.0,"rank":4,"service":"tidb-tikv","severity_z":105.541},{"evidence_source":"metric","onset_rel_s":900.0,"rank":5,"service":"tidb-tidb","severity_z":11.582},{"evidence_source":"metric","onset_rel_s":1080.0,"rank":6,"service":"adservice","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1080.0,"rank":7,"service":"cartservice","severity_z":18.288},{"evidence_source":"metric","onset_rel_s":1140.0,"rank":8,"service":"productcatalogservice","severity_z":22.866},{"evidence_source":"metric","onset_rel_s":1320.0,"rank":9,"service":"checkoutservice","severity_z":13.152},{"evidence_source":"metric","onset_rel_s":1440.0,"rank":10,"service":"shippingservice","severity_z":13.152},{"evidence_source":"metric","onset_rel_s":1740.0,"rank":11,"service":"k8s-master3","severity_z":12.0},{"evidence_source":"none","onset_rel_s":null,"rank":12,"service":"currencyservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":13,"service":"emailservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":14,"service":"paymentservice","severity_z":0.0}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"cartservice","caller":"checkoutservice"},{"callee":"emailservice","caller":"checkoutservice"},{"callee":"productcatalogservice","caller":"checkoutservice"},{"callee":"shippingservice","caller":"checkoutservice"},{"callee":"cartservice","caller":"frontend"},{"callee":"checkoutservice","caller":"frontend"},{"callee":"productcatalogservice","caller":"frontend"},{"callee":"recommendationservice","caller":"frontend"},{"callee":"shippingservice","caller":"frontend"},{"callee":"productcatalogservice","caller":"recommendationservice"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

[excluded before optimizer]

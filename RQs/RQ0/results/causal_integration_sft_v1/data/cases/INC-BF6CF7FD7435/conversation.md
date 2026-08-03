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
opaque_id: INC-BF6CF7FD7435
observation_window={"duration_rel_s":478.215,"source_metric_rows":950}
selection_summary={"candidate_count":104,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":901,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["loadgenerator","loadgenerator-d75cc479f-nkxqc","mysql","mysql-0","rabbitmq","rabbitmq-0","ts-admin-basic-info-service","ts-admin-basic-info-service-66cdcc94bc-tmp4j","ts-admin-order-service","ts-admin-order-service-5b6dc77d7d-pmq9t","ts-admin-route-service","ts-admin-route-service-f9c84f85f-bxnn7","ts-admin-travel-service","ts-admin-travel-service-659b5c9df4-2pj8h","ts-admin-user-service","ts-admin-user-service-5bfc8844b9-zwbvb","ts-assurance-service","ts-assurance-service-75c854dc5c-m8pc7","ts-auth-service","ts-auth-service-69bdd5df8-jjhk4","ts-avatar-service","ts-avatar-service-845b64df6-v28ln","ts-basic-service","ts-basic-service-7c6d59d5c4-n6vd8","ts-cancel-service","ts-cancel-service-7ffd988fdb-gk9d5","ts-config-service","ts-config-service-55cffbf48b-6qkrr","ts-consign-price-service","ts-consign-price-service-654cb4fc65-lqrqd","ts-consign-service","ts-consign-service-9954fddf-lnn5n","ts-contacts-service","ts-contacts-service-6d745b6c8f-k2mmw","ts-delivery-service","ts-delivery-service-694895c6cb-nktw8","ts-execute-service","ts-execute-service-8457c56cb7-gljj8","ts-food-delivery-service","ts-food-delivery-service-96d856899-j7gct","ts-food-service","ts-food-service-64d454885b-b7g9t","ts-gateway-service","ts-gateway-service-7f988fb8c4-vx72s","ts-inside-payment-service","ts-inside-payment-service-5ccb8ccb87-wgx9z","ts-news-service","ts-news-service-6d6c6d7855-nrz8m","ts-notification-service","ts-notification-service-58f6c468d7-h576x","ts-order-other-service","ts-order-other-service-5d6878687f-l8lvq","ts-order-service","ts-order-service-6794d6f564-p9llc","ts-payment-service","ts-payment-service-58854d694-96dpj","ts-preserve-other-service","ts-preserve-other-service-64fd9c88cf-c77wf","ts-preserve-service","ts-preserve-service-696df489d4-8pqf5","ts-price-service","ts-price-service-67c895b45-nh66r","ts-rebook-service","ts-rebook-service-7c7644bbdd-5lpxc","ts-route-plan-service","ts-route-plan-service-556cddc5c9-qgwq5","ts-route-service","ts-route-service-cfc6dbcf7-2ndsl","ts-seat-service","ts-seat-service-6c78b7d797-rnv72","ts-security-service","ts-security-service-55f5b777bb-jzkfh","ts-station-food-service","ts-station-food-service-746f6779d7-zvjhg","ts-station-service","ts-station-service-65986cc944-l9bdf","ts-ticket-office-service","ts-ticket-office-service-d7c58b8c7-8c6zq","ts-train-food-service","ts-train-food-service-d5485c677-z55w2","ts-train-service","ts-train-service-9b56d75b6-85np7","ts-travel-plan-service","ts-travel-plan-service-7875c49896-4xtpg","ts-travel-service","ts-travel-service-c7b5c6d9b-q2rxj","ts-travel2-service","ts-travel2-service-7ff5bbbf54-qr9n7","ts-ui-dashboard","ts-ui-dashboard-57867cb85c-9lnct","ts-user-service","ts-user-service-54dd6b48c-zlzn9","ts-verification-code-service","ts-verification-code-service-85785c4f79-lbwh2","ts-voucher-service","ts-voucher-service-689c4fc885-k2sgz","ts-wait-order-service","ts-wait-order-service-7cf6bc9468-8f492","worker1","worker2","worker3","worker4","worker5","worker6"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[3.736,11.208,18.68,26.152,33.624,41.097,48.569,56.041,63.513,70.985,78.457,85.929,93.401,100.873,108.345,115.818,123.29,130.762,138.234,145.706,153.178,160.65,168.122,175.594,183.066,190.539,198.011,205.483,212.955,220.427,227.899,235.371,242.843,250.315,257.788,265.26,272.732,280.204,287.676,295.148,302.62,310.092,317.564,325.036,332.509,339.981,347.453,354.925,362.397,369.869,377.341,384.813,392.285,399.757,407.23,414.702,422.174,429.646,437.118,444.59,452.062,459.534,467.006,474.478]
[M1] rank=1 service=ts-news-service metric=k8s.pod.memory.rss baseline=8032426.666667 peak=10391552.0 signed_z=86.02 onset_bin=59 onset_rel_s=444.59 persistence_bins=5
values_compact=rle:7995392*11,8052736*48,10387456*2,10391552*3
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,1,2,1,2,1,2,1,2,1,2
[M2] rank=2 service=ts-news-service metric=container.memory.rss baseline=7990272.0 peak=10350592.0 signed_z=85.021 onset_bin=60 onset_rel_s=452.062 persistence_bins=4
values_compact=rle:7954432*12,8011776*48,10350592*4
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,1,2,1,2,1,2,1,2,1,2
[M3] rank=3 service=ts-news-service metric=k8s.pod.memory.usage baseline=9649493.333333 peak=11595776.0 signed_z=65.184 onset_bin=59 onset_rel_s=444.59 persistence_bins=5
values_compact=rle:9609216*11,9670656*16,9674752*15,9689088*1,9703424*16,11595776*2,11587584*3
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,1,2,1,2,1,2,1,2,1,2
[M4] rank=4 service=ts-news-service metric=k8s.pod.memory.working_set baseline=9649493.333333 peak=11595776.0 signed_z=65.184 onset_bin=59 onset_rel_s=444.59 persistence_bins=5
values_compact=rle:9609216*11,9670656*16,9674752*15,9689088*1,9703424*16,11595776*2,11587584*3
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,1,2,1,2,1,2,1,2,1,2
[M5] rank=5 service=ts-news-service metric=k8s.pod.memory.node.utilization baseline=7.1e-05 peak=8.6e-05 signed_z=65.184 onset_bin=59 onset_rel_s=444.59 persistence_bins=5
values_compact=rle:0.000071*11,0.000072*48,0.000086*5
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,1,2,1,2,1,2,1,2,1,2
[M6] rank=6 service=ts-news-service metric=k8s.pod.memory_limit_utilization baseline=0.002996 peak=0.0036 signed_z=65.184 onset_bin=59 onset_rel_s=444.59 persistence_bins=5
values_compact=rle:0.002983*11,0.003002*16,0.003003*15,0.003008*1,0.003012*16,0.0036*2,0.003597*3
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,1,2,1,2,1,2,1,2,1,2
[M7] rank=7 service=ts-news-service metric=k8s.pod.memory.available baseline=3211575978.666667 peak=3209629696.0 signed_z=-65.184 onset_bin=59 onset_rel_s=444.59 persistence_bins=5
values_compact=rle:3211616256*11,3211554816*16,3211550720*15,3211536384*1,3211522048*16,3209629696*2,3209637888*3
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,1,2,1,2,1,2,1,2,1,2
[M8] rank=8 service=ts-news-service metric=container.memory.usage baseline=8964181.333333 peak=10903552.0 signed_z=64.136 onset_bin=60 onset_rel_s=452.062 persistence_bins=4
values_compact=rle:8925184*12,8986624*15,8990720*16,9019392*17,10903552*4
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,1,2,1,2,1,2,1,2,1,2
[M9] rank=9 service=ts-news-service metric=container.memory.working_set baseline=8964181.333333 peak=10903552.0 signed_z=64.136 onset_bin=60 onset_rel_s=452.062 persistence_bins=4
values_compact=rle:8925184*12,8986624*15,8990720*16,9019392*17,10903552*4
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,1,2,1,2,1,2,1,2,1,2
[M10] rank=10 service=ts-news-service metric=container.memory.available baseline=3212261290.666667 peak=3210321920.0 signed_z=-64.136 onset_bin=60 onset_rel_s=452.062 persistence_bins=4
values_compact=rle:3212300288*12,3212238848*15,3212234752*16,3212206080*17,3210321920*4
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,1,2,1,2,1,2,1,2,1,2
[M11] rank=11 service=ts-station-food-service metric=k8s.pod.cpu.node.utilization baseline=0.00027 peak=0.007666 signed_z=28.153 onset_bin=23 onset_rel_s=175.594 persistence_bins=3
values_compact=delta:0.000275,-0.000002,-0.000002,-0.000093,-0.000006,0.000029,0.000029,0,-0.000027,0,-0.000061,-0.000006,-0.000006,0,0.000043,0.000012,0.000012,-0.000004,-0.000005,0.00003,0.00003,-0.000009,-0.000009,0.001041,0,-0.001077,0.000097,0,0,-0.000124,-0.000021,0.000007,0.000008,0,-0.000022,0.000018,0.000018,0.000006,0.000006,-0.000028,-0.000028,0,0.000003,0,0,-0.000004,0.000148,0,-0.000118,0,0.000031,0,-0.000052,0,-0.000032,-0.000006,-0.000006,0.007571,-0.007602,0,0,0.000028,0,-0.000042
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M12] rank=12 service=ts-station-food-service metric=k8s.pod.cpu.usage baseline=0.034622 peak=0.981311 signed_z=28.153 onset_bin=23 onset_rel_s=175.594 persistence_bins=3
values_compact=delta:0.035194,-0.000261,-0.000262,-0.011944,-0.000718,0.003732,0.003732,0,-0.003448,0,-0.007858,-0.000765,-0.000765,0,0.005461,0.001587,0.001587,-0.000613,-0.000613,0.00383,0.00383,-0.001141,-0.00114,0.133323,0,-0.137871,0.012349,0,0,-0.015794,-0.002797,0.000997,0.000997,0,-0.002779,0.002277,0.002278,0.000765,0.000765,-0.003583,-0.003583,0,0.000363,0,0,-0.00048,0.018916,0,-0.015144,0,0.004077,0,-0.006756,0,-0.004112,-0.000712,-0.000712,0.969102,-0.973162,0,0,0.003624,0,-0.005431
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[436.18891954421997,476.11707067489624]

=== LOG SUMMARY ===
{"entries":[{"error_logs":6432,"error_pct":19.22,"service":"ts-seat-service","total_logs":33460},{"error_logs":650,"error_pct":16.23,"service":"ts-food-service","total_logs":4004},{"error_logs":244,"error_pct":5.7,"service":"ts-preserve-service","total_logs":4281},{"error_logs":242,"error_pct":1.99,"service":"ts-order-service","total_logs":12175},{"error_logs":96,"error_pct":25.0,"service":"ts-delivery-service","total_logs":384},{"error_logs":95,"error_pct":25.0,"service":"ts-notification-service","total_logs":380},{"error_logs":15,"error_pct":0.1,"service":"ts-ui-dashboard","total_logs":14921},{"error_logs":12,"error_pct":0.16,"service":"ts-travel2-service","total_logs":7424}],"mode":"errors","omitted_services":23,"service_count":31}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":920.8,"error_pct":0.0,"p95_during_ms":35.05756154999998,"p95_pre_ms":3.4343750499999994,"service":"ts-config-service","spans":32190},{"delta_pct":885.6,"error_pct":0.0,"p95_during_ms":3850.8819575,"p95_pre_ms":390.7222481499998,"service":"ts-route-plan-service","spans":3406},{"delta_pct":815.1,"error_pct":0.0,"p95_during_ms":4574.189734949999,"p95_pre_ms":499.88105279999996,"service":"ts-travel-plan-service","spans":4503},{"delta_pct":738.2,"error_pct":0.0,"p95_during_ms":35.45685580000001,"p95_pre_ms":4.229898899999999,"service":"ts-order-service","spans":32244},{"delta_pct":702.7,"error_pct":0.0,"p95_during_ms":30.858777999999987,"p95_pre_ms":3.84437665,"service":"ts-price-service","spans":9238},{"delta_pct":641.4,"error_pct":0.0,"p95_during_ms":26.828028000000003,"p95_pre_ms":3.61876405,"service":"ts-station-service","spans":16725},{"delta_pct":599.3,"error_pct":0.0,"p95_during_ms":34.51389295,"p95_pre_ms":4.9356997499999995,"service":"ts-train-food-service","spans":4840},{"delta_pct":565.5,"error_pct":0.0,"p95_during_ms":24.98189819999994,"p95_pre_ms":3.7537169999999995,"service":"ts-train-service","spans":21120}],"omitted_services":22,"service_count":30}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=35 omitted_edges=0
[{"evidence_source":"metric","onset_rel_s":415.2,"rank":1,"service":"ts-travel2-service","severity_z":27.105},{"evidence_source":"metric","onset_rel_s":433.8,"rank":2,"service":"ts-admin-travel-service","severity_z":15.534},{"evidence_source":"metric","onset_rel_s":441.0,"rank":3,"service":"ts-news-service","severity_z":86.02},{"evidence_source":"trace","onset_rel_s":443.4,"rank":4,"service":"ts-route-service","severity_z":12.306},{"evidence_source":"trace","onset_rel_s":443.4,"rank":5,"service":"ts-verification-code-service","severity_z":7.306},{"evidence_source":"trace","onset_rel_s":443.4,"rank":6,"service":"ts-user-service","severity_z":20.607},{"evidence_source":"trace","onset_rel_s":443.4,"rank":7,"service":"ts-order-service","severity_z":7.055},{"evidence_source":"metric","onset_rel_s":444.0,"rank":8,"service":"ts-basic-service","severity_z":18.538},{"evidence_source":"metric","onset_rel_s":448.2,"rank":9,"service":"ts-order-other-service","severity_z":18.576},{"evidence_source":"metric","onset_rel_s":448.8,"rank":10,"service":"ts-admin-route-service","severity_z":15.988},{"evidence_source":"trace","onset_rel_s":453.6,"rank":11,"service":"ts-station-food-service","severity_z":24.28},{"evidence_source":"trace","onset_rel_s":453.6,"rank":12,"service":"ts-route-plan-service","severity_z":6.976},{"evidence_source":"metric","onset_rel_s":463.8,"rank":13,"service":"ts-admin-user-service","severity_z":19.0},{"evidence_source":"trace","onset_rel_s":473.4,"rank":14,"service":"ts-consign-price-service","severity_z":26.737}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"ts-route-service","caller":"ts-basic-service"},{"callee":"ts-route-service","caller":"ts-route-plan-service"},{"callee":"ts-travel2-service","caller":"ts-route-plan-service"},{"callee":"ts-basic-service","caller":"ts-travel2-service"},{"callee":"ts-route-service","caller":"ts-travel2-service"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

[excluded before optimizer]

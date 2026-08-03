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
opaque_id: INC-37832D171656
observation_window={"duration_rel_s":477.503,"source_metric_rows":1079}
selection_summary={"candidate_count":104,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":1017,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["loadgenerator","loadgenerator-877c5fc96-gjwbn","mysql","mysql-0","rabbitmq","rabbitmq-0","ts-admin-basic-info-service","ts-admin-basic-info-service-65df4c5d86-858l6","ts-admin-order-service","ts-admin-order-service-7bb4f698d7-zwfdq","ts-admin-route-service","ts-admin-route-service-5b9fcdbf98-7frsz","ts-admin-travel-service","ts-admin-travel-service-7ccb4f69cf-482wq","ts-admin-user-service","ts-admin-user-service-56c4b4dcbd-7nlb9","ts-assurance-service","ts-assurance-service-5c77657bcb-d2j9d","ts-auth-service","ts-auth-service-cc77d6f9-lghqq","ts-avatar-service","ts-avatar-service-5454b669ff-p6cbb","ts-basic-service","ts-basic-service-dffc5b899-7bzht","ts-cancel-service","ts-cancel-service-697f84df75-qzdhr","ts-config-service","ts-config-service-7b97b98795-hdvfp","ts-consign-price-service","ts-consign-price-service-75f975bd76-f88tz","ts-consign-service","ts-consign-service-6857bf796d-lnvj9","ts-contacts-service","ts-contacts-service-bf469d8f6-5rvqz","ts-delivery-service","ts-delivery-service-6f495f545-8nj7x","ts-execute-service","ts-execute-service-65b69d766-hjk7j","ts-food-delivery-service","ts-food-delivery-service-777b64d578-7wdfg","ts-food-service","ts-food-service-59b5c65f89-nm2ld","ts-gateway-service","ts-gateway-service-847b8c9767-lxgz4","ts-inside-payment-service","ts-inside-payment-service-75ffb88dbb-8v2nt","ts-news-service","ts-news-service-7869d45c45-vct4s","ts-notification-service","ts-notification-service-78796d88d6-skkf4","ts-order-other-service","ts-order-other-service-6477b6cd98-86mlq","ts-order-service","ts-order-service-6f4cfb5df7-8trrf","ts-payment-service","ts-payment-service-64bdf8c88c-btvmh","ts-preserve-other-service","ts-preserve-other-service-8774fbf78-t9qm2","ts-preserve-service","ts-preserve-service-6f7ff8d889-22dzd","ts-price-service","ts-price-service-6d8564b588-78q5t","ts-rebook-service","ts-rebook-service-f996d677c-nfqn4","ts-route-plan-service","ts-route-plan-service-6d5c54cb74-sl7rt","ts-route-service","ts-route-service-c4496565b-7r4hw","ts-seat-service","ts-seat-service-94b957996-rgcz7","ts-security-service","ts-security-service-6d487fd867-nw4vb","ts-station-food-service","ts-station-food-service-585dfddcfd-whhhh","ts-station-service","ts-station-service-76f56dcbf-dtx5k","ts-ticket-office-service","ts-ticket-office-service-778556c8b6-dwksw","ts-train-food-service","ts-train-food-service-5975fbbccb-tmv9n","ts-train-service","ts-train-service-56bbd9b4c5-dpdwq","ts-travel-plan-service","ts-travel-plan-service-85b47db797-p9jvg","ts-travel-service","ts-travel-service-c588d796f-n2pqk","ts-travel2-service","ts-travel2-service-7565f66f4c-hft54","ts-ui-dashboard","ts-ui-dashboard-78c8f55d5d-ttbzt","ts-user-service","ts-user-service-6f674f6cc8-wxtjl","ts-verification-code-service","ts-verification-code-service-544d85fbb6-d7cmt","ts-voucher-service","ts-voucher-service-75f4db5b54-qxqrs","ts-wait-order-service","ts-wait-order-service-568568585c-ngt9p","worker1","worker2","worker3","worker4","worker5","worker6"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[3.73,11.191,18.652,26.113,33.574,41.035,48.496,55.957,63.418,70.879,78.34,85.801,93.262,100.723,108.184,115.645,123.106,130.567,138.028,145.489,152.95,160.411,167.872,175.333,182.794,190.255,197.716,205.177,212.638,220.099,227.56,235.021,242.482,249.943,257.404,264.865,272.326,279.787,287.248,294.709,302.17,309.631,317.092,324.553,332.014,339.475,346.936,354.397,361.858,369.319,376.78,384.241,391.702,399.163,406.624,414.085,421.546,429.007,436.468,443.929,451.39,458.851,466.312,473.773]
[M1] rank=1 service=ts-train-service metric=hubble_http_request_duration_p50_seconds baseline=0.003733 peak=0.876451 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.003656,-0.000433,0.001051,0.001018,-0.000684,-0.0014,-0.000246,-0.000323,0.000881,0.001641,-0.002375,0.873665,-0.871082,-0.002832,-0.000006,-0.000015
missing_mask_bits=0111011101110111011101110111011101110111011101110111011101110111
observed_counts_compact=csv:1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0
[M2] rank=2 service=ts-travel-plan-service metric=hubble_http_request_duration_p50_seconds baseline=0.006601 peak=10.0 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.003889,0.000534,0.002452,0.010625,-0.01,-0.003833,0.000708,0.000208,0.005417,9.99,0,0
missing_mask_bits=1101110111011101110111011101110111111101110111111101111111011111
observed_counts_compact=rle:0*2,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*7,1*1,0*3,1*1,0*7,1*1,0*7,1*1,0*5
[M3] rank=3 service=ts-price-service metric=hubble_http_request_duration_p95_seconds baseline=0.008925 peak=1.05 signed_z=909.691 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.00875,0.000615,0.000218,-0.000058,-0.000525,-0.003,0.003679,-0.000179,0.000121,0.000079,0.003,1.0373,-1.045118,0.002777,-0.002789,0.002059
missing_mask_bits=1110111011101110111011101110111011101110111011101110111011101110
observed_counts_compact=csv:0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1
[M4] rank=4 service=ts-travel-service metric=hubble_http_request_duration_p50_seconds baseline=0.030999 peak=10.0 signed_z=825.322 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.025,-0.003158,0.015658,0.020833,-0.020833,-0.014643,0.001072,-0.0029,0.003257,0.031964,7.44375,-2.5,5,-3.125,-2.8125
missing_mask_bits=0111011101110111011101110111011101110111011101110111111101110111
observed_counts_compact=rle:1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*7,1*1,0*3,1*1,0*3
[M5] rank=5 service=ts-route-plan-service metric=hubble_http_request_duration_p50_seconds baseline=0.035588 peak=10.0 signed_z=767.78 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.02425,-0.001295,0.006212,0.0375,-0.029167,0,-0.008333,0.008333,0.0375,-0.06625,9.99125,-7.5,7.5,0
missing_mask_bits=1101110111011101110111011101110111011101110111111101111111011101
observed_counts_compact=rle:0*2,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*7,1*1,0*7,1*1,0*3,1*1,0*1
[M6] rank=6 service=ts-travel2-service metric=hubble_http_request_duration_p50_seconds baseline=0.035417 peak=7.916667 signed_z=756.6 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.0375,0,0.020833,-0.020833,-0.0125,0.0125,-0.0125,0,0.041667,7.85,-1.416667,1,-1.625,-1.708333,2.864583,-2.65625
missing_mask_bits=0111011101110111011101110111011101110111011101110111011101110111
observed_counts_compact=csv:1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0
[M7] rank=7 service=ts-travel-service metric=hubble_http_request_duration_p90_seconds baseline=0.134908 peak=10.0 signed_z=236.568 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.098636,0.000739,0.115625,-0.12,0.05,0.0075,-0.05375,0.07625,0.00375,4.57125,5.25,-5.47625,0.22625,-0.25,3
missing_mask_bits=1101110111011101110111011101110111111110111011101110111011101110
observed_counts_compact=rle:0*2,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*8,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1
[M8] rank=8 service=ts-travel2-service metric=hubble_http_request_duration_p90_seconds baseline=0.171406 peak=10.0 signed_z=233.663 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.145,0.04875,0.02125,0.02,-0.06,0,-0.08,0.0425,9.195833,0.666667,-1,1,-0.666667,-1.333333,2,-5.25
missing_mask_bits=1101110111011101110111011101110111011110111011101110111011101110
observed_counts_compact=csv:0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1
[M9] rank=9 service=ts-travel2-service metric=hubble_http_request_duration_p95_seconds baseline=0.155906 peak=10.0 signed_z=177.588 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.16375,-0.06975,-0.0015,0.06825,0.06675,-0.0375,-0.1025,0.14375,0.00375,7.765,2,-0.25,0,0.25,-0.375,-2.1875
missing_mask_bits=1011101110111011101110111011101110111011101110111011101110111011
observed_counts_compact=csv:0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0
[M10] rank=10 service=ts-travel-service metric=hubble_http_request_duration_p95_seconds baseline=0.240312 peak=9.875 signed_z=112.973 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.221875,-0.001875,-0.035625,0.278125,-0.235,-0.04125,0.02125,0.005,0.9375,8.35,0.375,-0.375,-7.100625,7.100625,-2.0625
missing_mask_bits=1011101110111011101110111011101110111111101110111011101110111011
observed_counts_compact=rle:0*1,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*7,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*2
[M11] rank=11 service=ts-route-service metric=hubble_http_request_duration_p99_seconds baseline=0.061145 peak=4.2625 signed_z=69.082 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.017063,0.006777,0.000044,0.024022,-0.030681,0.055744,0.002431,0.135475,1.554125,-1.7419,-0.00485,4.24425,-2.28,-1.791,-0.02,0.059
missing_mask_bits=1011101110111011101110111011110111011101110111011101110111011101
observed_counts_compact=csv:0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0
[M12] rank=12 service=ts-price-service metric=hubble_http_request_duration_p99_seconds baseline=0.013029 peak=0.2975 signed_z=50.282 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.00955,0.000294,-0.000114,0.01332,-0.013165,-0.000035,0.01275,-0.012875,0.163775,-0.16364,0.00002,0.16812,-0.16155,-0.006995,0.288045,-0.288467
missing_mask_bits=1011101110111011101110111011110111011101110111011101110111011101
observed_counts_compact=csv:0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[285.0,435.0]

=== LOG SUMMARY ===
{"entries":[{"error_logs":5948,"error_pct":100.0,"service":"ts-ui-dashboard","total_logs":5948},{"error_logs":2486,"error_pct":10.08,"service":"ts-basic-service","total_logs":24665},{"error_logs":272,"error_pct":17.37,"service":"ts-food-service","total_logs":1566},{"error_logs":102,"error_pct":3.31,"service":"ts-travel2-service","total_logs":3081},{"error_logs":66,"error_pct":25.19,"service":"ts-notification-service","total_logs":262},{"error_logs":66,"error_pct":4.41,"service":"ts-preserve-service","total_logs":1498},{"error_logs":66,"error_pct":1.5,"service":"ts-order-service","total_logs":4388},{"error_logs":65,"error_pct":24.81,"service":"ts-delivery-service","total_logs":262}],"mode":"errors","omitted_services":23,"service_count":31}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":8891.3,"error_pct":53.57,"p95_during_ms":60722.322166549995,"p95_pre_ms":675.3458202499983,"service":"ts-route-plan-service","spans":1186},{"delta_pct":8789.5,"error_pct":0.0,"p95_during_ms":20000.651555099997,"p95_pre_ms":224.99064850000005,"service":"ts-ui-dashboard","spans":5947},{"delta_pct":8731.4,"error_pct":6.13,"p95_during_ms":20000.9693324,"p95_pre_ms":226.47503470000004,"service":"loadgenerator","spans":5947},{"delta_pct":6586.4,"error_pct":65.22,"p95_during_ms":60013.2259589,"p95_pre_ms":897.5428511999997,"service":"ts-travel-plan-service","spans":1598},{"delta_pct":5100.7,"error_pct":31.94,"p95_during_ms":8210.4834093,"p95_pre_ms":157.87390689999998,"service":"ts-travel-service","spans":6669},{"delta_pct":3912.4,"error_pct":35.5,"p95_during_ms":6318.3698423,"p95_pre_ms":157.471337,"service":"ts-travel2-service","spans":4668},{"delta_pct":-56.2,"error_pct":0.0,"p95_during_ms":10.799780199999995,"p95_pre_ms":24.675479699999975,"service":"ts-consign-service","spans":648},{"delta_pct":33.2,"error_pct":0.0,"p95_during_ms":6.841797599999998,"p95_pre_ms":5.136222500000001,"service":"ts-order-service","spans":11737}],"omitted_services":22,"service_count":30}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=35 omitted_edges=4
[{"evidence_source":"trace","onset_rel_s":293.4,"rank":1,"service":"ts-travel-service","severity_z":11.756},{"evidence_source":"metric","onset_rel_s":296.4,"rank":2,"service":"mysql","severity_z":22.546},{"evidence_source":"trace","onset_rel_s":303.6,"rank":3,"service":"ts-travel-plan-service","severity_z":3.532},{"evidence_source":"trace","onset_rel_s":303.6,"rank":4,"service":"ts-route-plan-service","severity_z":3.596},{"evidence_source":"trace","onset_rel_s":323.4,"rank":5,"service":"ts-station-service","severity_z":22.525},{"evidence_source":"metric","onset_rel_s":330.0,"rank":6,"service":"ts-train-service","severity_z":999.0},{"evidence_source":"trace","onset_rel_s":333.0,"rank":7,"service":"ts-travel2-service","severity_z":5.136},{"evidence_source":"metric","onset_rel_s":343.8,"rank":8,"service":"ts-route-service","severity_z":69.082},{"evidence_source":"metric","onset_rel_s":345.6,"rank":9,"service":"ts-admin-basic-info-service","severity_z":12.946},{"evidence_source":"metric","onset_rel_s":345.6,"rank":10,"service":"ts-contacts-service","severity_z":12.946},{"evidence_source":"metric","onset_rel_s":345.6,"rank":11,"service":"ts-execute-service","severity_z":12.946},{"evidence_source":"metric","onset_rel_s":353.4,"rank":12,"service":"ts-price-service","severity_z":909.691},{"evidence_source":"metric","onset_rel_s":370.2,"rank":13,"service":"ts-basic-service","severity_z":49.735},{"evidence_source":"trace","onset_rel_s":432.6,"rank":14,"service":"ts-seat-service","severity_z":14.03}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"ts-price-service","caller":"ts-basic-service"},{"callee":"ts-route-service","caller":"ts-basic-service"},{"callee":"ts-station-service","caller":"ts-basic-service"},{"callee":"ts-train-service","caller":"ts-basic-service"},{"callee":"ts-route-service","caller":"ts-route-plan-service"},{"callee":"ts-travel-service","caller":"ts-route-plan-service"},{"callee":"ts-travel2-service","caller":"ts-route-plan-service"},{"callee":"ts-route-plan-service","caller":"ts-travel-plan-service"},{"callee":"ts-seat-service","caller":"ts-travel-plan-service"},{"callee":"ts-train-service","caller":"ts-travel-plan-service"},{"callee":"ts-basic-service","caller":"ts-travel-service"},{"callee":"ts-route-service","caller":"ts-travel-service"},{"callee":"ts-seat-service","caller":"ts-travel-service"},{"callee":"ts-basic-service","caller":"ts-travel2-service"},{"callee":"ts-route-service","caller":"ts-travel2-service"},{"callee":"ts-seat-service","caller":"ts-travel2-service"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

[excluded before optimizer]

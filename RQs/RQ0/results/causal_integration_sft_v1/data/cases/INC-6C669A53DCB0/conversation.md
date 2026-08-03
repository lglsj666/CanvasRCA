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
opaque_id: INC-6C669A53DCB0
observation_window={"duration_rel_s":479.025,"source_metric_rows":951}
selection_summary={"candidate_count":104,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":902,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["loadgenerator","loadgenerator-7c6465b994-jg55n","mysql","mysql-0","rabbitmq","rabbitmq-0","ts-admin-basic-info-service","ts-admin-basic-info-service-8498cf659d-wlqh2","ts-admin-order-service","ts-admin-order-service-5f48c9847-dbmk6","ts-admin-route-service","ts-admin-route-service-67f9bbcd98-s6vbb","ts-admin-travel-service","ts-admin-travel-service-7d676d8cf-fkmpm","ts-admin-user-service","ts-admin-user-service-5f875c8488-7rbjk","ts-assurance-service","ts-assurance-service-6b6f9549bd-hfc6q","ts-auth-service","ts-auth-service-54bd57586c-kk7wq","ts-avatar-service","ts-avatar-service-697c966bc9-cdvjn","ts-basic-service","ts-basic-service-599dcbcd59-wprxn","ts-cancel-service","ts-cancel-service-5d6f598b75-64zhq","ts-config-service","ts-config-service-788886954c-fvgfl","ts-consign-price-service","ts-consign-price-service-65d465fbbd-gzcfv","ts-consign-service","ts-consign-service-f89c85c6-gj678","ts-contacts-service","ts-contacts-service-746b87fbc6-jvjzz","ts-delivery-service","ts-delivery-service-669dcd76fc-tt75t","ts-execute-service","ts-execute-service-565f5cf898-zjt95","ts-food-delivery-service","ts-food-delivery-service-6fcc5f49db-6nftq","ts-food-service","ts-food-service-5dd9757985-qhztk","ts-gateway-service","ts-gateway-service-df699cb95-8zl9p","ts-inside-payment-service","ts-inside-payment-service-69459cf8c4-cgxwx","ts-news-service","ts-news-service-6d6c6d7855-m4rvp","ts-notification-service","ts-notification-service-7967657c5d-fh4pn","ts-order-other-service","ts-order-other-service-86c75649c4-pcpnk","ts-order-service","ts-order-service-554d59f5c-4wqb2","ts-payment-service","ts-payment-service-66bfbd95f5-9mpzc","ts-preserve-other-service","ts-preserve-other-service-6bbdcb9df4-vdf88","ts-preserve-service","ts-preserve-service-87fbbf5b5-s9zs5","ts-price-service","ts-price-service-54b6b4b96-cjqkl","ts-rebook-service","ts-rebook-service-7f8fd67745-8njrz","ts-route-plan-service","ts-route-plan-service-76fc6cc974-b4vmg","ts-route-service","ts-route-service-799f648896-42lqn","ts-seat-service","ts-seat-service-675c89f44-g46fm","ts-security-service","ts-security-service-6868bb5d87-m5np5","ts-station-food-service","ts-station-food-service-59fc9cbf74-29lqd","ts-station-service","ts-station-service-96ccf6fc-68twp","ts-ticket-office-service","ts-ticket-office-service-58c97df4b6-6hqlw","ts-train-food-service","ts-train-food-service-bcf66b6d8-q9wsc","ts-train-service","ts-train-service-6bdbdb4547-5682f","ts-travel-plan-service","ts-travel-plan-service-5b7fb74b4f-7j2s8","ts-travel-service","ts-travel-service-74794d67b9-8fbkj","ts-travel2-service","ts-travel2-service-6659b8fd5f-b86gt","ts-ui-dashboard","ts-ui-dashboard-59499f7b8b-7ltdw","ts-user-service","ts-user-service-87d8d9d54-d2l4z","ts-verification-code-service","ts-verification-code-service-6c9f97cb54-5sbfb","ts-voucher-service","ts-voucher-service-6f9ddf4fc4-gm74b","ts-wait-order-service","ts-wait-order-service-bbf549d5-xtkx5","worker1","worker2","worker3","worker4","worker5","worker6"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[3.742,11.227,18.712,26.197,33.681,41.166,48.651,56.136,63.621,71.105,78.59,86.075,93.56,101.044,108.529,116.014,123.499,130.983,138.468,145.953,153.438,160.923,168.407,175.892,183.377,190.862,198.346,205.831,213.316,220.801,228.285,235.77,243.255,250.74,258.225,265.709,273.194,280.679,288.164,295.648,303.133,310.618,318.103,325.588,333.072,340.557,348.042,355.527,363.011,370.496,377.981,385.466,392.95,400.435,407.92,415.405,422.89,430.374,437.859,445.344,452.829,460.313,467.798,475.283]
[M1] rank=1 service=ts-auth-service-54bd57586c-kk7wq metric=k8s.container.restarts baseline=0.0 peak=1.0 signed_z=999.0 onset_bin=33 onset_rel_s=250.74 persistence_bins=23
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0001000100010001000100010001000100010001000100010001000100010001
observed_counts_compact=csv:1,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0
[M2] rank=2 service=ts-auth-service metric=container.filesystem.usage baseline=466944.0 peak=0.0 signed_z=-999.0 onset_bin=32 onset_rel_s=243.255 persistence_bins=12
values_compact=rle:466944*32,0*1,69632*2,256000*1,442368*6,446464*1,456704*1,466944*20
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M3] rank=3 service=ts-food-delivery-service metric=k8s.pod.cpu.node.utilization baseline=4e-05 peak=0.005888 signed_z=825.045 onset_bin=38 onset_rel_s=288.164 persistence_bins=5
values_compact=delta:0.000063,-0.00001,-0.00001,0,-0.000001,-0.000002,-0.000002,0.000007,0.000007,-0.000005,-0.000004,0,-0.000004,0,-0.000002,0,0.000006,-0.000005,-0.000005,-0.000001,-0.000002,0.000002,0.000002,0,0.000006,-0.000004,-0.000003,0.000003,0,0.000002,0.000003,0,0.000012,-0.000003,-0.000004,0.000003,0.000002,0.000008,0.000008,0,-0.00001,-0.000004,-0.000004,0.00292,0.002919,-0.002926,-0.002925,0.000002,0.000002,0.000007,0,-0.000015,0,-0.000001,0.000001,0.000006,0.000006,0,-0.000012,0,-0.000001,0,0,0
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M4] rank=4 service=ts-food-delivery-service metric=k8s.pod.cpu.usage baseline=0.005107 peak=0.75365 signed_z=825.045 onset_bin=38 onset_rel_s=288.164 persistence_bins=5
values_compact=delta:0.008073,-0.001274,-0.001274,-0.000079,-0.00008,-0.000246,-0.000246,0.000907,0.000908,-0.000618,-0.000618,0,-0.000424,0,-0.000252,0,0.000734,-0.000665,-0.000666,-0.000142,-0.000142,0.0002,0.0002,0,0.000812,-0.000463,-0.000463,0.000427,0,0.000313,0.000313,0,0.001584,-0.000438,-0.000438,0.000313,0.000312,0.00102,0.00102,0,-0.001308,-0.000503,-0.000503,0.373678,0.373678,-0.374486,-0.374486,0.000304,0.000304,0.000889,0,-0.001995,0,-0.000082,0.000068,0.000818,0.000818,0,-0.001533,0,-0.000224,0,0.000013,0
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M5] rank=5 service=ts-food-delivery-service metric=k8s.pod.cpu_limit_utilization baseline=0.001021 peak=0.15073 signed_z=825.045 onset_bin=38 onset_rel_s=288.164 persistence_bins=5
values_compact=delta:0.001615,-0.000255,-0.000255,-0.000016,-0.000016,-0.000049,-0.000049,0.000181,0.000182,-0.000124,-0.000123,0,-0.000085,0,-0.000051,0,0.000147,-0.000133,-0.000133,-0.000028,-0.000029,0.00004,0.00004,0,0.000163,-0.000093,-0.000093,0.000086,0,0.000062,0.000063,0,0.000317,-0.000088,-0.000087,0.000062,0.000063,0.000204,0.000204,0,-0.000262,-0.000101,-0.0001,0.074735,0.074736,-0.074897,-0.074897,0.00006,0.000061,0.000178,0,-0.000399,0,-0.000016,0.000013,0.000164,0.000163,0,-0.000306,0,-0.000045,0,0.000003,0
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M6] rank=6 service=ts-food-delivery-service metric=container.cpu.usage baseline=0.005252 peak=0.483679 signed_z=532.095 onset_bin=37 onset_rel_s=280.679 persistence_bins=7
values_compact=delta:0.007652,-0.001124,-0.001125,0.000011,0.000012,-0.000269,-0.000269,0.000855,0.000855,0,-0.001369,0,0,-0.00022,0,0.000579,0,-0.000606,-0.000607,0,-0.000488,0.000259,0.00026,0.000431,0.000431,-0.000479,-0.000479,0,0.000284,0,0.001954,0,0,-0.000282,0,0.000011,0,0.002334,0.000495,0,0,-0.003173,0.000226,0,0,0.47752,0,-0.239259,-0.239258,0.000271,0.00027,-0.000844,-0.000844,0,0.000156,0,0.001117,0,0,-0.001025,0,-0.000263,0,0.001359
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M7] rank=7 service=ts-auth-service metric=k8s.pod.memory.rss baseline=764130730.666667 peak=40960.0 signed_z=-146.936 onset_bin=32 onset_rel_s=243.255 persistence_bins=30
values_compact=delta:755974144,0,2506752,0,114688,262144,262144,0,20480,0,0,1544192,0,4012032,4012032,-3817472,-3817472,1105920,0,9777152,0,-4022272,0,159744,0,4386816,-3883008,51200,51200,0,36864,0,-768696320,0,0,239050752,45686784,0,212791296,0,0,92520448,50221056,0,0,116195328,0,24031232,0,3860480,3860480,2633728,2633728,0,3153920,0,466944,7032832,7032832,-2226176,-2226176,1056768,0,202752
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M8] rank=8 service=ts-auth-service metric=k8s.pod.memory.node.utilization baseline=0.005747 peak=9e-06 signed_z=-144.734 onset_bin=32 onset_rel_s=243.255 persistence_bins=30
values_compact=delta:0.005686,0,0.000018,0,0.000001,0.000002,0.000002,0,0,0,0,0.000012,0,0.000029,0.00003,-0.000028,-0.000029,0.000009,0,0.000074,0,-0.000026,0,0.000003,0,0.000029,-0.000032,0,0,0,0.000001,0,-0.005772,0,0,0.001828,0.000344,0,0.001596,0,0,0.000719,0.000332,0,0,0.000974,0,0.000089,0,0.000021,0.00002,0.00002,0.000019,0,0.000024,0,0.000005,0.000052,0.000052,-0.000018,-0.000019,0.000008,0,0.000002
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M9] rank=9 service=ts-auth-service metric=k8s.pod.memory.usage baseline=776076032.0 peak=1159168.0 signed_z=-144.734 onset_bin=32 onset_rel_s=243.255 persistence_bins=30
values_compact=delta:767750144,0,2506752,0,114688,280576,280576,0,8192,0,0,1544192,0,3995648,3995648,-3817472,-3817472,1126400,0,10039296,0,-3489792,0,372736,0,3883008,-4349952,55296,55296,0,20480,0,-779395072,0,0,246902784,46452736,0,215445504,0,0,97099776,44851200,0,0,131567616,0,11997184,0,2764800,2764800,2646016,2646016,0,3190784,0,696320,7020544,7020544,-2486272,-2486272,1052672,0,331776
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M10] rank=10 service=ts-auth-service metric=k8s.pod.memory_limit_utilization baseline=0.240926 peak=0.00036 signed_z=-144.734 onset_bin=32 onset_rel_s=243.255 persistence_bins=30
values_compact=delta:0.238341,0,0.000778,0,0.000036,0.000087,0.000087,0,0.000003,0,0,0.000479,0,0.00124,0.001241,-0.001185,-0.001185,0.000349,0,0.003117,0,-0.001084,0,0.000116,0,0.001206,-0.001351,0.000017,0.000018,0,0.000006,0,-0.241956,0,0,0.076649,0.01442,0,0.066883,0,0,0.030144,0.013924,0,0,0.040844,0,0.003724,0,0.000859,0.000858,0.000821,0.000822,0,0.00099,0,0.000216,0.00218,0.002179,-0.000771,-0.000772,0.000326,0,0.000103
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M11] rank=11 service=ts-auth-service metric=k8s.pod.memory.available baseline=2445534464.0 peak=3220385792.0 signed_z=144.721 onset_bin=32 onset_rel_s=243.255 persistence_bins=30
values_compact=delta:2453860352,0,-2506752,0,-114688,-280576,-280576,0,-8192,0,0,-1544192,0,-3995648,-3995648,3817472,3817472,-1126400,0,-10039296,0,3489792,0,-372736,0,-3883008,4349952,-55296,-55296,0,-20480,0,779329536,0,0,-246870016,-46100480,0,-215445504,0,0,-97099776,-44851200,0,0,-131567616,0,-11997184,0,-2764800,-2764800,-2646016,-2646016,0,-3190784,0,-696320,-7020544,-7020544,2486272,2486272,-1052672,0,-331776
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M12] rank=12 service=ts-auth-service metric=k8s.pod.memory.working_set baseline=775691008.0 peak=839680.0 signed_z=-144.721 onset_bin=32 onset_rel_s=243.255 persistence_bins=30
values_compact=delta:767365120,0,2506752,0,114688,280576,280576,0,8192,0,0,1544192,0,3995648,3995648,-3817472,-3817472,1126400,0,10039296,0,-3489792,0,372736,0,3883008,-4349952,55296,55296,0,20480,0,-779329536,0,0,246870016,46100480,0,215445504,0,0,97099776,44851200,0,0,131567616,0,11997184,0,2764800,2764800,2646016,2646016,0,3190784,0,696320,7020544,7020544,-2486272,-2486272,1052672,0,331776
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[240.00773310661316,469.999906539917]

=== LOG SUMMARY ===
{"entries":[{"error_logs":5048,"error_pct":19.25,"service":"ts-seat-service","total_logs":26227},{"error_logs":2904,"error_pct":18.08,"service":"ts-ui-dashboard","total_logs":16058},{"error_logs":508,"error_pct":16.4,"service":"ts-food-service","total_logs":3098},{"error_logs":200,"error_pct":2.14,"service":"ts-order-service","total_logs":9366},{"error_logs":200,"error_pct":6.23,"service":"ts-preserve-service","total_logs":3208},{"error_logs":96,"error_pct":25.0,"service":"ts-delivery-service","total_logs":384},{"error_logs":96,"error_pct":25.0,"service":"ts-notification-service","total_logs":384},{"error_logs":10,"error_pct":100.0,"service":"mysql","total_logs":10}],"mode":"errors","omitted_services":24,"service_count":32}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":-38.1,"error_pct":0.0,"p95_during_ms":332.12027444999995,"p95_pre_ms":536.3014658,"service":"ts-route-plan-service","spans":2619},{"delta_pct":-34.9,"error_pct":0.0,"p95_during_ms":421.5681016000001,"p95_pre_ms":647.4059600999997,"service":"ts-travel-plan-service","spans":3505},{"delta_pct":-34.8,"error_pct":0.0,"p95_during_ms":62.43507084999998,"p95_pre_ms":95.74266259999985,"service":"ts-travel-service","spans":14165},{"delta_pct":-32.7,"error_pct":0.0,"p95_during_ms":2.5985926999999993,"p95_pre_ms":3.859241249999999,"service":"ts-config-service","spans":25250},{"delta_pct":-31.8,"error_pct":0.0,"p95_during_ms":119.77827054999982,"p95_pre_ms":175.7133711999999,"service":"ts-ui-dashboard","spans":14605},{"delta_pct":-31.6,"error_pct":18.99,"p95_during_ms":120.61561149999991,"p95_pre_ms":176.42671739999992,"service":"loadgenerator","spans":14605},{"delta_pct":-30.1,"error_pct":0.0,"p95_during_ms":11.241473399999997,"p95_pre_ms":16.075111999999997,"service":"ts-seat-service","spans":20932},{"delta_pct":-26.4,"error_pct":0.0,"p95_during_ms":18.317511749999994,"p95_pre_ms":24.88974759999999,"service":"ts-security-service","spans":2450}],"omitted_services":22,"service_count":30}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=35 omitted_edges=0
[{"evidence_source":"metric","onset_rel_s":250.2,"rank":1,"service":"ts-auth-service","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":280.8,"rank":2,"service":"ts-admin-user-service","severity_z":11.775},{"evidence_source":"metric","onset_rel_s":280.8,"rank":3,"service":"ts-contacts-service","severity_z":11.775},{"evidence_source":"metric","onset_rel_s":280.8,"rank":4,"service":"ts-order-other-service","severity_z":11.775},{"evidence_source":"metric","onset_rel_s":280.8,"rank":5,"service":"ts-preserve-other-service","severity_z":11.775},{"evidence_source":"metric","onset_rel_s":280.8,"rank":6,"service":"ts-route-plan-service","severity_z":11.775},{"evidence_source":"metric","onset_rel_s":280.8,"rank":7,"service":"ts-ticket-office-service","severity_z":11.775},{"evidence_source":"metric","onset_rel_s":328.2,"rank":8,"service":"ts-food-delivery-service","severity_z":825.045},{"evidence_source":"metric","onset_rel_s":352.8,"rank":9,"service":"ts-preserve-service","severity_z":15.619},{"evidence_source":"metric","onset_rel_s":416.4,"rank":10,"service":"ts-avatar-service","severity_z":14.08},{"evidence_source":"trace","onset_rel_s":434.4,"rank":11,"service":"ts-user-service","severity_z":16.799},{"evidence_source":"metric","onset_rel_s":451.2,"rank":12,"service":"ts-news-service","severity_z":18.614},{"evidence_source":"metric","onset_rel_s":472.2,"rank":13,"service":"ts-rebook-service","severity_z":16.064},{"evidence_source":"metric","onset_rel_s":477.6,"rank":14,"service":"ts-consign-service","severity_z":27.889}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"ts-contacts-service","caller":"ts-preserve-service"},{"callee":"ts-user-service","caller":"ts-preserve-service"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

{"confidence":"medium","reason":"Rank ts-auth-service first because ts-auth-service has direct k8s.container.restarts evidence (signed-z 999, persistence 23 bins); ts-admin-user-service is second despite propagation rank 2 because onset ordering alone does not establish the causal origin.","services":["ts-auth-service","ts-admin-user-service"]}

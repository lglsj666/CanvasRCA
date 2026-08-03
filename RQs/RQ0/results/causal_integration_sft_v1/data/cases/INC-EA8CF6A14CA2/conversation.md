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
opaque_id: INC-EA8CF6A14CA2
observation_window={"duration_rel_s":477.282,"source_metric_rows":951}
selection_summary={"candidate_count":104,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":902,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["loadgenerator","loadgenerator-76c5949c78-k4hgq","mysql","mysql-0","rabbitmq","rabbitmq-0","ts-admin-basic-info-service","ts-admin-basic-info-service-579bc4cd8d-2wcc8","ts-admin-order-service","ts-admin-order-service-76fc4c68d5-8m5kt","ts-admin-route-service","ts-admin-route-service-85bffd5f6-f88w2","ts-admin-travel-service","ts-admin-travel-service-797ccbcff7-sl4qk","ts-admin-user-service","ts-admin-user-service-7874ccc7c4-zwr2v","ts-assurance-service","ts-assurance-service-d87bf675d-bd7mt","ts-auth-service","ts-auth-service-6477f4967c-6hrsn","ts-avatar-service","ts-avatar-service-74fd5ff4c7-2586p","ts-basic-service","ts-basic-service-59f887c7d5-kgjqm","ts-cancel-service","ts-cancel-service-67454d8789-576ld","ts-config-service","ts-config-service-56457f8db5-bxd6s","ts-consign-price-service","ts-consign-price-service-54b69c6854-55d9n","ts-consign-service","ts-consign-service-686f9c998-mkpds","ts-contacts-service","ts-contacts-service-7df9fc84b6-2zsbw","ts-delivery-service","ts-delivery-service-55b55bb555-hhpqk","ts-execute-service","ts-execute-service-64b744d564-jmnf7","ts-food-delivery-service","ts-food-delivery-service-599dfbdb6d-v6kjl","ts-food-service","ts-food-service-755696bb9f-7rtkd","ts-gateway-service","ts-gateway-service-9cdfbbdfc-jgskv","ts-inside-payment-service","ts-inside-payment-service-7666f6c64d-557zd","ts-news-service","ts-news-service-7869d45c45-9tftt","ts-notification-service","ts-notification-service-b5b74bb44-h9w6t","ts-order-other-service","ts-order-other-service-67cbddcb88-27sg8","ts-order-service","ts-order-service-85b9979d59-x2sdc","ts-payment-service","ts-payment-service-5df5775665-qb5w2","ts-preserve-other-service","ts-preserve-other-service-74f69f9db4-tx2k6","ts-preserve-service","ts-preserve-service-7f8d678dcf-9b477","ts-price-service","ts-price-service-c4b84c894-7mx2z","ts-rebook-service","ts-rebook-service-776674d89f-kqtz9","ts-route-plan-service","ts-route-plan-service-7f4b79f79b-mfqsb","ts-route-service","ts-route-service-6db4bdfd5d-zt2gm","ts-seat-service","ts-seat-service-5dddf49dfd-m6cnn","ts-security-service","ts-security-service-69797c9fdf-mwkhl","ts-station-food-service","ts-station-food-service-6c88c88456-zzkwl","ts-station-service","ts-station-service-75dc8bb94c-rztx7","ts-ticket-office-service","ts-ticket-office-service-7cd6fff84-zqgfh","ts-train-food-service","ts-train-food-service-5cb6b7d98b-tvcfp","ts-train-service","ts-train-service-6ccc6f4465-djlsl","ts-travel-plan-service","ts-travel-plan-service-56754fc8bc-vvx89","ts-travel-service","ts-travel-service-5577469b95-hlxts","ts-travel2-service","ts-travel2-service-859b87cf49-zfw96","ts-ui-dashboard","ts-ui-dashboard-897fdb6b4-2nqsq","ts-user-service","ts-user-service-7fdd6fdfb8-k66jq","ts-verification-code-service","ts-verification-code-service-5795bcf896-mhth8","ts-voucher-service","ts-voucher-service-6db9df749b-x5b45","ts-wait-order-service","ts-wait-order-service-5b9fcd797f-hclzv","worker1","worker2","worker3","worker4","worker5","worker6"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[3.729,11.186,18.644,26.101,33.559,41.016,48.474,55.931,63.389,70.847,78.304,85.762,93.219,100.677,108.134,115.592,123.049,130.507,137.964,145.422,152.879,160.337,167.794,175.252,182.71,190.167,197.625,205.082,212.54,219.997,227.455,234.912,242.37,249.827,257.285,264.742,272.2,279.657,287.115,294.573,302.03,309.488,316.945,324.403,331.86,339.318,346.775,354.233,361.69,369.148,376.605,384.063,391.52,398.978,406.436,413.893,421.351,428.808,436.266,443.723,451.181,458.638,466.096,473.553]
[M1] rank=1 service=ts-order-service-85b9979d59-x2sdc metric=k8s.container.restarts baseline=0.0 peak=1.0 signed_z=999.0 onset_bin=34 onset_rel_s=257.285 persistence_bins=23
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0100010001000100010001000100010001000100010001001000100010001000
observed_counts_compact=csv:1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1
[M2] rank=2 service=ts-order-service metric=container.filesystem.usage baseline=466944.0 peak=0.0 signed_z=-999.0 onset_bin=32 onset_rel_s=242.37 persistence_bins=13
values_compact=rle:466944*32,0*1,69632*4,442368*8,466944*19
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,1,2,1,2
[M3] rank=3 service=rabbitmq metric=k8s.pod.memory.rss baseline=152541098.666667 peak=153788416.0 signed_z=609.571 onset_bin=43 onset_rel_s=324.403 persistence_bins=21
values_compact=rle:152539136*16,152541184*1,152543232*26,153788416*2,152547328*14,152625152*2,152547328*3
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,1,2,1,2,1,2,1,2,1,2
[M4] rank=4 service=ts-order-service metric=k8s.pod.memory.usage baseline=825057109.333333 peak=130998272.0 signed_z=-465.499 onset_bin=32 onset_rel_s=242.37 persistence_bins=30
values_compact=delta:824311808,0,18432,18432,538624,538624,0,-905216,0,1748992,0,0,200704,0,-3268608,983040,0,0,-667648,0,651264,0,-368640,0,-49152,962560,0,0,2473984,0,1871872,0,-698060800,0,57767936,57767936,22687744,22687744,74926080,74926080,58976256,58976256,0,59424768,0,103792640,0,65265664,0,0,11235328,0,8294400,0,901120,901120,274432,274432,0,12099584,0,-2801664,0,522240
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,1,2,1,2
[M5] rank=5 service=ts-order-service metric=k8s.pod.memory_limit_utilization baseline=0.192099 peak=0.0305 signed_z=-465.499 onset_bin=32 onset_rel_s=242.37 persistence_bins=30
values_compact=delta:0.191925,0,0.000004,0.000005,0.000125,0.000125,0,-0.00021,0,0.000407,0,0,0.000047,0,-0.000761,0.000228,0,0,-0.000155,0,0.000152,0,-0.000086,0,-0.000012,0.000225,0,0,0.000576,0,0.000435,0,-0.16253,0,0.013451,0.01345,0.005282,0.005283,0.017445,0.017445,0.013731,0.013732,0,0.013836,0,0.024166,0,0.015196,0,0,0.002615,0,0.001932,0,0.000209,0.00021,0.000064,0.000064,0,0.002817,0,-0.000652,0,0.000121
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,1,2,1,2
[M6] rank=6 service=ts-order-service metric=k8s.pod.memory.node.utilization baseline=0.00611 peak=0.00097 signed_z=-465.499 onset_bin=32 onset_rel_s=242.37 persistence_bins=30
values_compact=delta:0.006105,0,0,0,0.000004,0.000004,0,-0.000007,0,0.000013,0,0,0.000002,0,-0.000025,0.000008,0,0,-0.000005,0,0.000005,0,-0.000003,0,-0.000001,0.000008,0,0,0.000018,0,0.000014,0,-0.00517,0,0.000428,0.000428,0.000168,0.000168,0.000555,0.000555,0.000436,0.000437,0,0.00044,0,0.000769,0,0.000483,0,0,0.000083,0,0.000062,0,0.000006,0.000007,0.000002,0.000002,0,0.00009,0,-0.000021,0,0.000004
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,1,2,1,2
[M7] rank=7 service=ts-order-service metric=k8s.pod.memory.available baseline=3470295210.666667 peak=4164321280.0 signed_z=465.477 onset_bin=32 onset_rel_s=242.37 persistence_bins=30
values_compact=delta:3471040512,0,-18432,-18432,-538624,-538624,0,905216,0,-1748992,0,0,-200704,0,3268608,-983040,0,0,667648,0,-651264,0,368640,0,49152,-962560,0,0,-2473984,0,-1871872,0,698028032,0,-57767936,-57767936,-22511616,-22511616,-74926080,-74926080,-58976256,-58976256,0,-59424768,0,-103792640,0,-65265664,0,0,-11235328,0,-8294400,0,-901120,-901120,-274432,-274432,0,-12099584,0,2801664,0,-522240
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,1,2,1,2
[M8] rank=8 service=ts-order-service metric=k8s.pod.memory.working_set baseline=824672085.333333 peak=130646016.0 signed_z=-465.477 onset_bin=32 onset_rel_s=242.37 persistence_bins=30
values_compact=delta:823926784,0,18432,18432,538624,538624,0,-905216,0,1748992,0,0,200704,0,-3268608,983040,0,0,-667648,0,651264,0,-368640,0,-49152,962560,0,0,2473984,0,1871872,0,-698028032,0,57767936,57767936,22511616,22511616,74926080,74926080,58976256,58976256,0,59424768,0,103792640,0,65265664,0,0,11235328,0,8294400,0,901120,901120,274432,274432,0,12099584,0,-2801664,0,522240
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,1,2,1,2
[M9] rank=9 service=ts-order-service metric=k8s.pod.memory.rss baseline=812922453.333333 peak=122114048.0 signed_z=-438.858 onset_bin=32 onset_rel_s=242.37 persistence_bins=30
values_compact=delta:811929600,0,155648,155648,143360,143360,0,147456,0,1744896,0,0,196608,0,-3293184,188416,0,0,131072,0,118784,0,94208,0,12288,966656,0,0,2203648,0,2129920,0,-695054336,0,57724928,57724928,22333440,22333440,74405888,74405888,58200064,58200064,0,59662336,0,93929472,0,71802880,0,0,13324288,0,8126464,0,1370112,1370112,282624,282624,0,10850304,0,-1830912,0,509952
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,1,2,1,2
[M10] rank=10 service=ts-order-service metric=container.memory.working_set baseline=823865002.666667 peak=211279872.0 signed_z=-388.044 onset_bin=32 onset_rel_s=242.37 persistence_bins=31
values_compact=delta:822769664,-10240,0,319488,133120,133120,53248,53248,1208320,0,342016,342016,2195456,-5427200,0,0,196608,393216,0,102400,-114688,-114688,823296,823296,-1286144,696320,0,2727936,-206848,-206848,0,2031616,-616697856,33513472,397312,1187840,0,0,58974208,0,124393472,124393472,27766784,0,53622784,53622784,90591232,0,7604224,7604224,0,11038720,0,1413120,167936,167936,598016,0,0,10723328,24178688,0,0,-24084480
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,1,2,1,2
[M11] rank=11 service=ts-order-service metric=container.memory.rss baseline=812858197.333333 peak=237346816.0 signed_z=-380.222 onset_bin=34 onset_rel_s=257.285 persistence_bins=30
values_compact=delta:811806720,147456,0,319488,114688,114688,61440,61440,1224704,0,335872,335872,1437696,-4698112,0,0,204800,131072,0,98304,10240,10240,47104,47104,12288,966656,0,2203648,0,0,0,2134016,-579780608,1445888,0,0,56791040,0,122314752,122314752,29261824,0,54517760,54517760,75714560,0,13959168,13959168,0,12541952,0,1409024,440320,440320,540672,0,0,10362880,22745088,0,0,-23044096
missing_mask_bits=0000000000000000000000000000000011000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,0,0,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,1,2,1,2
[M12] rank=12 service=ts-order-service metric=container.memory.usage baseline=824250026.666667 peak=245223424.0 signed_z=-366.786 onset_bin=34 onset_rel_s=257.285 persistence_bins=29
values_compact=delta:823154688,-10240,0,319488,133120,133120,53248,53248,1208320,0,342016,342016,2195456,-5427200,0,0,196608,393216,0,102400,-114688,-114688,823296,823296,-1286144,696320,0,2727936,-206848,-206848,0,2031616,-583139328,1187840,0,0,59326464,0,124393472,124393472,27766784,0,53622784,53622784,90591232,0,7604224,7604224,0,11038720,0,1413120,167936,167936,598016,0,0,10723328,24178688,0,0,-24084480
missing_mask_bits=0000000000000000000000000000000011000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,0,0,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,1,2,1,2

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[235.5402798652649,475.5405578613281]

=== LOG SUMMARY ===
{"entries":[{"error_logs":5077,"error_pct":19.35,"service":"ts-seat-service","total_logs":26242},{"error_logs":578,"error_pct":17.32,"service":"ts-food-service","total_logs":3337},{"error_logs":472,"error_pct":3.6,"service":"ts-ui-dashboard","total_logs":13094},{"error_logs":184,"error_pct":2.1,"service":"ts-order-service","total_logs":8766},{"error_logs":179,"error_pct":5.73,"service":"ts-preserve-service","total_logs":3123},{"error_logs":78,"error_pct":0.62,"service":"ts-travel-service","total_logs":12658},{"error_logs":65,"error_pct":25.0,"service":"ts-notification-service","total_logs":260},{"error_logs":65,"error_pct":25.29,"service":"ts-delivery-service","total_logs":257}],"mode":"errors","omitted_services":24,"service_count":32}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":-89.2,"error_pct":0.0,"p95_during_ms":33.53712479999999,"p95_pre_ms":311.300116,"service":"ts-food-service","spans":3354},{"delta_pct":-63.1,"error_pct":0.0,"p95_during_ms":498.051335,"p95_pre_ms":1348.1258215999999,"service":"ts-preserve-service","spans":2029},{"delta_pct":-38.0,"error_pct":0.0,"p95_during_ms":15.4983605,"p95_pre_ms":24.99370239999996,"service":"ts-consign-service","spans":878},{"delta_pct":-26.6,"error_pct":0.0,"p95_during_ms":7.7492895,"p95_pre_ms":10.562868,"service":"ts-station-food-service","spans":2472},{"delta_pct":-21.2,"error_pct":0.0,"p95_during_ms":13.503211199999996,"p95_pre_ms":17.1346389,"service":"ts-payment-service","spans":530},{"delta_pct":-21.1,"error_pct":0.0,"p95_during_ms":6.990047449999998,"p95_pre_ms":8.85646875,"service":"ts-assurance-service","spans":1008},{"delta_pct":-18.9,"error_pct":0.0,"p95_during_ms":44.5732932,"p95_pre_ms":54.9602295,"service":"ts-cancel-service","spans":45},{"delta_pct":-15.0,"error_pct":0.0,"p95_during_ms":4.826835,"p95_pre_ms":5.68099245,"service":"ts-contacts-service","spans":5183}],"omitted_services":22,"service_count":30}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=35 omitted_edges=1
[{"evidence_source":"metric","onset_rel_s":246.0,"rank":1,"service":"ts-user-service","severity_z":14.198},{"evidence_source":"trace","onset_rel_s":253.8,"rank":2,"service":"loadgenerator","severity_z":6.422},{"evidence_source":"trace","onset_rel_s":253.8,"rank":3,"service":"ts-route-plan-service","severity_z":6.251},{"evidence_source":"trace","onset_rel_s":253.8,"rank":4,"service":"ts-travel2-service","severity_z":14.926},{"evidence_source":"metric","onset_rel_s":265.2,"rank":5,"service":"ts-train-food-service","severity_z":36.77},{"evidence_source":"metric","onset_rel_s":282.0,"rank":6,"service":"ts-admin-basic-info-service","severity_z":12.634},{"evidence_source":"trace","onset_rel_s":283.2,"rank":7,"service":"ts-seat-service","severity_z":10.596},{"evidence_source":"metric","onset_rel_s":317.4,"rank":8,"service":"ts-news-service","severity_z":13.42},{"evidence_source":"metric","onset_rel_s":320.4,"rank":9,"service":"ts-auth-service","severity_z":19.353},{"evidence_source":"metric","onset_rel_s":322.2,"rank":10,"service":"ts-travel-plan-service","severity_z":11.331},{"evidence_source":"metric","onset_rel_s":325.2,"rank":11,"service":"rabbitmq","severity_z":609.571},{"evidence_source":"trace","onset_rel_s":343.2,"rank":12,"service":"ts-order-service","severity_z":390.163},{"evidence_source":"metric","onset_rel_s":346.8,"rank":13,"service":"mysql","severity_z":22.424},{"evidence_source":"metric","onset_rel_s":421.8,"rank":14,"service":"ts-preserve-service","severity_z":15.422}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"ts-order-service","caller":"ts-preserve-service"},{"callee":"ts-seat-service","caller":"ts-preserve-service"},{"callee":"ts-user-service","caller":"ts-preserve-service"},{"callee":"ts-travel2-service","caller":"ts-route-plan-service"},{"callee":"ts-order-service","caller":"ts-seat-service"},{"callee":"ts-route-plan-service","caller":"ts-travel-plan-service"},{"callee":"ts-seat-service","caller":"ts-travel-plan-service"},{"callee":"ts-seat-service","caller":"ts-travel2-service"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

{"confidence":"high","reason":"Rank ts-order-service first because ts-order-service has direct k8s.container.restarts evidence (signed-z 999, persistence 23 bins); although ts-seat-service is salient, the caller path ts-seat-service -> ts-order-service means a disturbance in the callee can propagate back toward that caller-side symptom.","services":["ts-order-service","ts-seat-service"]}

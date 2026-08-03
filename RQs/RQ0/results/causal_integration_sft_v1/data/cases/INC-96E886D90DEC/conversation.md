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
opaque_id: INC-96E886D90DEC
observation_window={"duration_rel_s":479.165,"source_metric_rows":1079}
selection_summary={"candidate_count":104,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":999,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["loadgenerator","loadgenerator-b479bdc5c-b5sjb","mysql","mysql-0","rabbitmq","rabbitmq-0","ts-admin-basic-info-service","ts-admin-basic-info-service-96954787-s78mv","ts-admin-order-service","ts-admin-order-service-6bcf6ddf78-9vnlq","ts-admin-route-service","ts-admin-route-service-9678dfbb7-vj6q7","ts-admin-travel-service","ts-admin-travel-service-5f7dcc8c78-sdkh9","ts-admin-user-service","ts-admin-user-service-5b6598696f-vgsd7","ts-assurance-service","ts-assurance-service-5d8974b465-wjvjk","ts-auth-service","ts-auth-service-6d4cb476f4-qxkrg","ts-avatar-service","ts-avatar-service-7d44f9cdb-t8qbs","ts-basic-service","ts-basic-service-67bb4cc894-fw4sz","ts-cancel-service","ts-cancel-service-c464f54db-nw6mv","ts-config-service","ts-config-service-688bb57f66-lt9ns","ts-consign-price-service","ts-consign-price-service-7cd56448d5-4wgd4","ts-consign-service","ts-consign-service-858fd6988f-4mw9x","ts-contacts-service","ts-contacts-service-69f8874897-7vflq","ts-delivery-service","ts-delivery-service-8495b4886d-9cqnv","ts-execute-service","ts-execute-service-98d6db6b7-2j54r","ts-food-delivery-service","ts-food-delivery-service-6965df9cb7-zbc82","ts-food-service","ts-food-service-5bc8874bdd-zh7rt","ts-gateway-service","ts-gateway-service-7646b44946-ntm62","ts-inside-payment-service","ts-inside-payment-service-7f65df9f55-2rxfx","ts-news-service","ts-news-service-b7d748896-bxfzz","ts-notification-service","ts-notification-service-7f945dc747-v75xb","ts-order-other-service","ts-order-other-service-bdb88b855-g9sl2","ts-order-service","ts-order-service-6f4cfb5df7-4rzxl","ts-payment-service","ts-payment-service-767777d6bb-h5pp8","ts-preserve-other-service","ts-preserve-other-service-6cc7bb5679-66hq6","ts-preserve-service","ts-preserve-service-c9c68bb7b-2ldfz","ts-price-service","ts-price-service-75f657ff49-8mj5j","ts-rebook-service","ts-rebook-service-58c459f6d-74jtd","ts-route-plan-service","ts-route-plan-service-6cb49854ff-wkf4m","ts-route-service","ts-route-service-5495898fcc-84bqk","ts-seat-service","ts-seat-service-695f74448f-fdn4t","ts-security-service","ts-security-service-67d6f6c4fd-hwk8h","ts-station-food-service","ts-station-food-service-79b8d75b55-bddxm","ts-station-service","ts-station-service-5747c84884-cwqw4","ts-ticket-office-service","ts-ticket-office-service-f4fcd85cf-kk6nw","ts-train-food-service","ts-train-food-service-cddfc5cd9-hd5qz","ts-train-service","ts-train-service-b7b76f69d-t85jn","ts-travel-plan-service","ts-travel-plan-service-5c66f9b8dd-fwdzw","ts-travel-service","ts-travel-service-5d8d96b796-g6png","ts-travel2-service","ts-travel2-service-76d77f447d-gzzcx","ts-ui-dashboard","ts-ui-dashboard-677db5896c-lptds","ts-user-service","ts-user-service-8f5c8f8f5-4767n","ts-verification-code-service","ts-verification-code-service-7f9b649959-kzchq","ts-voucher-service","ts-voucher-service-f479849c9-9swwt","ts-wait-order-service","ts-wait-order-service-67c96d8684-f6gw5","worker1","worker2","worker3","worker4","worker5","worker6"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[3.743,11.23,18.717,26.204,33.691,41.178,48.665,56.152,63.639,71.126,78.613,86.1,93.587,101.074,108.561,116.048,123.535,131.022,138.509,145.996,153.483,160.969,168.456,175.943,183.43,190.917,198.404,205.891,213.378,220.865,228.352,235.839,243.326,250.813,258.3,265.787,273.274,280.761,288.248,295.735,303.222,310.709,318.196,325.682,333.169,340.656,348.143,355.63,363.117,370.604,378.091,385.578,393.065,400.552,408.039,415.526,423.013,430.5,437.987,445.474,452.961,460.448,467.935,475.422]
[M1] rank=1 service=ts-train-food-service metric=hubble_http_request_duration_p99_seconds baseline=0.009914 peak=2.395 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.00995,0,-0.000008,-0.000092,0.000063,-0.000046,0.000053,0.000005,-0.000037,0.000045,-0.000058,-0.000325,0.000325,0.000008,2.385117,-2.3712
missing_mask_bits=0111011101110111011101110111011101111011101110111011101110111011
observed_counts_compact=csv:1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0
[M2] rank=2 service=ts-verification-code-service metric=hubble_http_request_duration_p95_seconds baseline=0.00475 peak=0.0075 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.00475,0,0,0,0,0,0,0,0,0,0,0,0,0,0.00275,-0.00256
missing_mask_bits=0111011101110111011101110111011101110111011101110111011101110111
observed_counts_compact=csv:1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0
[M3] rank=3 service=ts-order-service metric=hubble_http_request_duration_p90_seconds baseline=0.007215 peak=0.6525 signed_z=678.565 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.007217,-0.000752,0.001347,0.000081,0.000145,-0.001788,0.002217,-0.002889,-0.000595,0.001517,-0.00125,-0.00075,0.00075,0.001583,0.000875,0.644792
missing_mask_bits=1011101110111011101110111011101110111011101110111011101110111011
observed_counts_compact=csv:0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0
[M4] rank=4 service=ts-consign-price-service metric=k8s.pod.cpu.node.utilization baseline=5e-05 peak=0.004004 signed_z=181.735 onset_bin=47 onset_rel_s=355.63 persistence_bins=2
values_compact=delta:0.000082,-0.000048,0.000013,0.000014,0,0.000001,-0.000013,-0.000013,-0.000005,0,0.000018,0.000018,-0.000018,-0.000019,0,-0.000001,0.000036,0,-0.000028,0,-0.000004,-0.000003,-0.000002,0,0.000008,0.00005,0,-0.000015,0.000015,0.000014,-0.000068,0,0.000021,-0.000002,0,-0.00002,0,0,-0.000001,0,0.000004,0,0,0,-0.000004,0,-0.000001,0.003975,-0.001988,-0.001988,0.000001,0.000001,0.000002,0.000002,-0.000003,0,0.000025,-0.000018,0.000002,0.000001,-0.000003,0,-0.000007,0.000013
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1
[M5] rank=5 service=ts-consign-price-service metric=k8s.pod.cpu.usage baseline=0.006387 peak=0.512547 signed_z=181.735 onset_bin=47 onset_rel_s=355.63 persistence_bins=2
values_compact=delta:0.0105,-0.006161,0.00171,0.001711,0.000066,0.000066,-0.001673,-0.001672,-0.0006,0,0.002295,0.002295,-0.002325,-0.002325,-0.000057,-0.000058,0.00451,0,-0.003559,0,-0.000467,-0.000468,-0.00025,0,0.001058,0.006358,0,-0.001842,0.001842,0.001842,-0.008652,0,0.002676,-0.000319,0,-0.002535,0,0,-0.000074,0,0.000403,0,0.000066,0,-0.000575,0,-0.000051,0.508812,-0.25448,-0.25448,0.000136,0.000135,0.000225,0.000225,-0.000336,0,0.003193,-0.002339,0.00024,0.000239,-0.000467,0,-0.000842,0.001639
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1
[M6] rank=6 service=ts-consign-price-service metric=k8s.pod.cpu_limit_utilization baseline=0.001277 peak=0.102509 signed_z=181.735 onset_bin=47 onset_rel_s=355.63 persistence_bins=2
values_compact=delta:0.0021,-0.001232,0.000342,0.000342,0.000013,0.000013,-0.000334,-0.000335,-0.00012,0,0.000459,0.000459,-0.000465,-0.000465,-0.000011,-0.000012,0.000902,0,-0.000711,0,-0.000094,-0.000093,-0.00005,0,0.000211,0.001272,0,-0.000369,0.000369,0.000368,-0.00173,0,0.000535,-0.000064,0,-0.000507,0,0,-0.000015,0,0.000081,0,0.000013,0,-0.000115,0,-0.00001,0.101762,-0.050896,-0.050896,0.000028,0.000027,0.000045,0.000045,-0.000068,0,0.000639,-0.000468,0.000048,0.000048,-0.000093,0,-0.000169,0.000328
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1
[M7] rank=7 service=ts-consign-price-service metric=container.cpu.usage baseline=0.006422 peak=0.361339 signed_z=128.28 onset_bin=47 onset_rel_s=355.63 persistence_bins=2
values_compact=delta:0.011783,-0.007196,0,0.002066,0,0,-0.000446,-0.001464,0.000806,0.000807,0.001235,0.001234,-0.002459,-0.002458,0.000639,0.00064,0,0.000993,0,0,-0.002293,0,-0.000135,-0.000134,0.001794,0.001795,0.000233,0,0.006875,0,-0.009786,0,0.00194,0.00194,-0.002239,-0.002238,0,-0.000081,0,0.000553,0.000004,0.000005,0,-0.000637,0,-0.000079,0,0.357642,-0.178862,-0.178863,0,0.000501,0,0.000068,0,0.001712,0,-0.001074,0,0.00046,-0.000304,-0.000305,-0.000646,0
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1
[M8] rank=8 service=ts-train-food-service metric=k8s.pod.cpu.node.utilization baseline=0.000136 peak=0.004702 signed_z=123.887 onset_bin=31 onset_rel_s=235.839 persistence_bins=6
values_compact=delta:0.000133,0.000018,-0.000016,-0.000016,-0.000003,-0.000003,-0.00001,0,0.000038,0.000042,0,0,-0.000024,0,-0.000047,0,0.000005,0,0.000031,0,0.000027,0,-0.00007,0,0.000031,-0.000019,0,-0.000036,0,0.00003,0.00007,0.000071,0,-0.00013,0,-0.000043,0,0.000003,0,0.000012,0,-0.000007,0,0,0.000062,0,-0.000079,0,0.000005,0,0.000586,0,-0.000596,0.000015,0,0.000068,0,0,0.004554,0,-0.004626,0.000004,0,-0.000002
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1
[M9] rank=9 service=ts-train-food-service metric=k8s.pod.cpu.usage baseline=0.017355 peak=0.601895 signed_z=123.887 onset_bin=31 onset_rel_s=235.839 persistence_bins=6
values_compact=delta:0.016985,0.002289,-0.00201,-0.002011,-0.000425,-0.000426,-0.001252,0,0.004878,0.005392,0,0,-0.003011,0,-0.006115,0,0.000638,0,0.003992,0,0.003431,0,-0.0089,0,0.003973,-0.00249,0,-0.004544,0,0.003762,0.00905,0.009051,0,-0.016669,0,-0.005452,0,0.000396,0,0.001563,0,-0.000937,0,0,0.007867,0,-0.010046,0,0.000607,0,0.075058,0,-0.076322,0.001877,0,0.008752,0,0,0.582944,0,-0.592124,0.000498,0,-0.000332
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1
[M10] rank=10 service=ts-train-food-service metric=k8s.pod.cpu_limit_utilization baseline=0.003471 peak=0.120379 signed_z=123.887 onset_bin=31 onset_rel_s=235.839 persistence_bins=6
values_compact=delta:0.003397,0.000458,-0.000402,-0.000402,-0.000085,-0.000086,-0.00025,0,0.000976,0.001078,0,0,-0.000602,0,-0.001223,0,0.000127,0,0.000799,0,0.000686,0,-0.00178,0,0.000795,-0.000498,0,-0.000909,0,0.000752,0.00181,0.00181,0,-0.003333,0,-0.001091,0,0.000079,0,0.000313,0,-0.000187,0,0,0.001573,0,-0.002009,0,0.000121,0,0.015012,0,-0.015265,0.000376,0,0.00175,0,0,0.116589,0,-0.118425,0.0001,0,-0.000067
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1
[M11] rank=11 service=ts-route-service metric=hubble_http_request_duration_p95_seconds baseline=0.009669 peak=0.02005 signed_z=102.857 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.00965,0.000125,0.000021,-0.000193,0.00019,-0.000178,0.000005,-0.00012,0.00001,0.000187,-0.000233,0.000262,-0.000132,0.000372,0.010084,-0.00105
missing_mask_bits=0111011101110111011101110111011101110111011101110111011101110111
observed_counts_compact=csv:1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0
[M12] rank=12 service=ts-train-food-service metric=container.cpu.usage baseline=0.018422 peak=0.537005 signed_z=96.398 onset_bin=50 onset_rel_s=378.091 persistence_bins=7
values_compact=delta:0.021086,0,-0.002015,0,-0.005029,0,0.000369,0,0.002619,0.008588,0,0,-0.005993,-0.00481,0,-0.001189,0.001368,0.001369,0.006596,0,-0.001349,-0.001349,-0.002615,-0.002614,0.000851,0,-0.003309,0,-0.001304,0,0.020845,0,-0.018944,0,0.00308,0,-0.003109,-0.00311,0.003239,-0.002024,0,0,0.001355,0,0.002138,0.002137,-0.003421,-0.003421,-0.000178,0,0.061181,0,-0.031006,-0.031007,0.00308,0,0.5249,0,-0.316051,0,-0.210731,-0.000503,0.000299,0.000298
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[397.03899669647217,457.03899669647217]

=== LOG SUMMARY ===
{"entries":[{"error_logs":5693,"error_pct":100.0,"service":"ts-ui-dashboard","total_logs":5693},{"error_logs":263,"error_pct":17.08,"service":"ts-food-service","total_logs":1540},{"error_logs":96,"error_pct":25.0,"service":"ts-delivery-service","total_logs":384},{"error_logs":95,"error_pct":25.0,"service":"ts-notification-service","total_logs":380},{"error_logs":24,"error_pct":2.56,"service":"ts-preserve-service","total_logs":936},{"error_logs":24,"error_pct":0.58,"service":"ts-order-service","total_logs":4126}],"mode":"errors","omitted_services":25,"service_count":31}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":140.0,"error_pct":0.0,"p95_during_ms":14.677025899999967,"p95_pre_ms":6.115535599999999,"service":"ts-contacts-service","spans":2035},{"delta_pct":93.6,"error_pct":0.0,"p95_during_ms":31.04150875,"p95_pre_ms":16.037158700000003,"service":"ts-seat-service","spans":9659},{"delta_pct":80.5,"error_pct":0.0,"p95_during_ms":74.82591860000001,"p95_pre_ms":41.450962800000006,"service":"ts-food-service","spans":1621},{"delta_pct":73.2,"error_pct":0.0,"p95_during_ms":7.367003499999995,"p95_pre_ms":4.25461215,"service":"ts-price-service","spans":2910},{"delta_pct":68.9,"error_pct":1.99,"p95_during_ms":335.5042352999975,"p95_pre_ms":198.63180259999965,"service":"loadgenerator","spans":11424},{"delta_pct":66.1,"error_pct":0.0,"p95_during_ms":8.896813349999993,"p95_pre_ms":5.3548065000000005,"service":"ts-train-food-service","spans":1803},{"delta_pct":62.1,"error_pct":0.0,"p95_during_ms":680.8544409,"p95_pre_ms":420.09363819999976,"service":"ts-route-plan-service","spans":1336},{"delta_pct":57.6,"error_pct":0.0,"p95_during_ms":895.6072568,"p95_pre_ms":568.3282325,"service":"ts-travel-plan-service","spans":1803}],"omitted_services":22,"service_count":30}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=35 omitted_edges=2
[{"evidence_source":"metric","onset_rel_s":355.2,"rank":1,"service":"ts-consign-price-service","severity_z":181.735},{"evidence_source":"trace","onset_rel_s":414.0,"rank":2,"service":"ts-train-food-service","severity_z":18.53},{"evidence_source":"trace","onset_rel_s":414.0,"rank":3,"service":"ts-food-service","severity_z":71.931},{"evidence_source":"trace","onset_rel_s":414.0,"rank":4,"service":"ts-config-service","severity_z":7.687},{"evidence_source":"trace","onset_rel_s":414.0,"rank":5,"service":"ts-seat-service","severity_z":15.428},{"evidence_source":"trace","onset_rel_s":414.0,"rank":6,"service":"ts-station-service","severity_z":35.4},{"evidence_source":"metric","onset_rel_s":421.2,"rank":7,"service":"ts-verification-code-service","severity_z":999.0},{"evidence_source":"trace","onset_rel_s":424.2,"rank":8,"service":"ts-price-service","severity_z":9.654},{"evidence_source":"trace","onset_rel_s":434.4,"rank":9,"service":"ts-user-service","severity_z":105.775},{"evidence_source":"trace","onset_rel_s":434.4,"rank":10,"service":"ts-route-service","severity_z":4.091},{"evidence_source":"trace","onset_rel_s":434.4,"rank":11,"service":"ts-contacts-service","severity_z":79.22},{"evidence_source":"metric","onset_rel_s":442.8,"rank":12,"service":"ts-auth-service","severity_z":54.759},{"evidence_source":"metric","onset_rel_s":464.4,"rank":13,"service":"ts-order-service","severity_z":678.565},{"evidence_source":"trace","onset_rel_s":474.0,"rank":14,"service":"ts-ui-dashboard","severity_z":4.513}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"ts-verification-code-service","caller":"ts-auth-service"},{"callee":"ts-train-food-service","caller":"ts-food-service"},{"callee":"ts-config-service","caller":"ts-seat-service"},{"callee":"ts-order-service","caller":"ts-seat-service"},{"callee":"ts-auth-service","caller":"ts-ui-dashboard"},{"callee":"ts-contacts-service","caller":"ts-ui-dashboard"},{"callee":"ts-food-service","caller":"ts-ui-dashboard"},{"callee":"ts-order-service","caller":"ts-ui-dashboard"},{"callee":"ts-route-service","caller":"ts-ui-dashboard"},{"callee":"ts-user-service","caller":"ts-ui-dashboard"},{"callee":"ts-verification-code-service","caller":"ts-ui-dashboard"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

[excluded before optimizer]

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
opaque_id: INC-DA5BC67DD48C
observation_window={"duration_rel_s":478.381,"source_metric_rows":1076}
selection_summary={"candidate_count":104,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":1008,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["loadgenerator","loadgenerator-5d4f49c7df-rr2qn","mysql","mysql-0","rabbitmq","rabbitmq-0","ts-admin-basic-info-service","ts-admin-basic-info-service-577d9b6494-7gv2v","ts-admin-order-service","ts-admin-order-service-7897899b9f-fjrvc","ts-admin-route-service","ts-admin-route-service-58bfc5cfcd-h48gs","ts-admin-travel-service","ts-admin-travel-service-7656f7bd5f-mfbmk","ts-admin-user-service","ts-admin-user-service-84cd877bbd-4mfmm","ts-assurance-service","ts-assurance-service-f7b884c6-5pxss","ts-auth-service","ts-auth-service-5db57c8fc9-p62f2","ts-avatar-service","ts-avatar-service-6986f5597c-5m6b4","ts-basic-service","ts-basic-service-7f6d959755-ff8mt","ts-cancel-service","ts-cancel-service-5fcb6975c5-ppg2t","ts-config-service","ts-config-service-7ff4bcc859-f64tm","ts-consign-price-service","ts-consign-price-service-6d4997bb56-stnl4","ts-consign-service","ts-consign-service-5c78f79656-29hdl","ts-contacts-service","ts-contacts-service-66f5db7796-58b5v","ts-delivery-service","ts-delivery-service-78bb4449d9-s2nl7","ts-execute-service","ts-execute-service-547b6fb74b-hv8fq","ts-food-delivery-service","ts-food-delivery-service-59b6766794-ndbm8","ts-food-service","ts-food-service-6998b4bf85-94xdx","ts-gateway-service","ts-gateway-service-8675b6c575-9hlbz","ts-inside-payment-service","ts-inside-payment-service-5f45b4cf4b-jrdsp","ts-news-service","ts-news-service-b7d748896-6rctv","ts-notification-service","ts-notification-service-684b567d54-r4gxp","ts-order-other-service","ts-order-other-service-6d4568c67d-5j9pn","ts-order-service","ts-order-service-bf7548fd8-bprl9","ts-payment-service","ts-payment-service-74bfdf98dc-mm54n","ts-preserve-other-service","ts-preserve-other-service-5b897b6d74-zs5nm","ts-preserve-service","ts-preserve-service-75c657bdc7-n2mzc","ts-price-service","ts-price-service-57984b7c8d-pgb27","ts-rebook-service","ts-rebook-service-58799f7b97-hxk5k","ts-route-plan-service","ts-route-plan-service-5fdb7c87c8-jxq4p","ts-route-service","ts-route-service-794d78b55b-82p4l","ts-seat-service","ts-seat-service-56455c6b6d-zwwbk","ts-security-service","ts-security-service-7d9675b88c-dgft9","ts-station-food-service","ts-station-food-service-6979d48fd6-wxhss","ts-station-service","ts-station-service-86fc99c77-6kwt7","ts-ticket-office-service","ts-ticket-office-service-58c7b9789b-5wjk7","ts-train-food-service","ts-train-food-service-c56498cfb-445gj","ts-train-service","ts-train-service-77f9c6464c-sqb78","ts-travel-plan-service","ts-travel-plan-service-6cbb7cbb89-22ccw","ts-travel-service","ts-travel-service-f6b67689-ftx9d","ts-travel2-service","ts-travel2-service-789c8887cf-ctvjg","ts-ui-dashboard","ts-ui-dashboard-9c5b7b7d4-499ph","ts-user-service","ts-user-service-7956998c46-fvgj4","ts-verification-code-service","ts-verification-code-service-5ccb47f48b-bxrvk","ts-voucher-service","ts-voucher-service-56bdc97988-tcmjf","ts-wait-order-service","ts-wait-order-service-b5f7d5577-xll2l","worker1","worker2","worker3","worker4","worker5","worker6"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[3.737,11.212,18.687,26.161,33.636,41.111,48.586,56.06,63.535,71.01,78.484,85.959,93.434,100.908,108.383,115.858,123.333,130.807,138.282,145.757,153.231,160.706,168.181,175.655,183.13,190.605,198.08,205.554,213.029,220.504,227.978,235.453,242.928,250.402,257.877,265.352,272.827,280.301,287.776,295.251,302.725,310.2,317.675,325.149,332.624,340.099,347.574,355.048,362.523,369.998,377.472,384.947,392.422,399.896,407.371,414.846,422.32,429.795,437.27,444.745,452.219,459.694,467.169,474.643]
[M1] rank=1 service=ts-voucher-service metric=k8s.pod.memory.node.utilization baseline=0.000297 peak=0.000297 signed_z=999.0 onset_bin=0 onset_rel_s=3.737 persistence_bins=64
values_compact=rle:0.000297*64
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M2] rank=2 service=ts-ui-dashboard metric=hubble_http_request_duration_p50_seconds baseline=0.028372 peak=5.0 signed_z=655.934 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.03379,0.012657,-0.02228,0,0.003333,-0.00375,-0.000042,-0.000262,-0.013654,-0.001875,3.742083,-3.708125,0.000469,-0.025469,4.983125
missing_mask_bits=1110111011101110111011101110111011101110111011101110111011101111
observed_counts_compact=rle:0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*4
[M3] rank=3 service=ts-preserve-service metric=k8s.pod.filesystem.usage baseline=588032.0 peak=12283904.0 signed_z=240.759 onset_bin=33 onset_rel_s=250.402 persistence_bins=31
values_compact=delta:507904,8192,0,8192,0,8192,8192,6144,6144,6144,2048,0,4096,4096,4096,4096,8192,4096,4096,4096,8192,8192,4096,6144,10240,4096,4096,6144,6144,8192,4096,6144,6144,507904,458752,450560,352256,491520,344064,327680,524288,319488,401408,425984,360448,491520,425984,376832,311296,458752,327680,0,131072,458752,393216,294912,393216,483328,286720,393216,442368,266240,311296,327680
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M4] rank=4 service=ts-order-other-service metric=hubble_http_request_duration_p99_seconds baseline=0.016225 peak=2.08 signed_z=168.555 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.046,-0.03605,0,0.01465,-0.014696,-0.000093,-0.000094,0.00015,-0.000817,0.40095,-0.40505,0,0.0041,0.000075,2.070875
missing_mask_bits=1110111011101110111011101110111011101110111011101110111011101111
observed_counts_compact=rle:0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*4
[M5] rank=5 service=ts-delivery-service metric=k8s.pod.cpu.node.utilization baseline=7.1e-05 peak=0.001702 signed_z=146.144 onset_bin=58 onset_rel_s=437.27 persistence_bins=3
values_compact=delta:0.00006,0.000003,0.000003,0,-0.000002,0.000004,0.000003,0,0,-0.000001,-0.000007,0,0.000029,0,-0.00001,0,-0.000008,0,0.000007,0,-0.00001,-0.00001,0.000003,0.000002,0.000032,-0.000045,0.000004,0.000004,0.000007,0.000006,0,-0.000016,0,0,-0.000002,0,0.000007,0,0.000001,0,0.000002,0.000003,-0.000003,0,0.000005,0,0.000004,0.000004,0.000001,0,-0.000009,-0.000009,0.000006,0.000006,-0.000011,-0.000011,0.000004,0.000003,0.000822,0.000821,-0.000813,-0.000813,0,0.000001
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1
[M6] rank=6 service=ts-delivery-service metric=k8s.pod.cpu.usage baseline=0.009131 peak=0.217841 signed_z=146.144 onset_bin=58 onset_rel_s=437.27 persistence_bins=3
values_compact=delta:0.007704,0.000402,0.000401,0,-0.000314,0.000474,0.000475,0,-0.000112,-0.000113,-0.000914,0,0.003763,0,-0.001211,0,-0.001052,0,0.000908,0,-0.001305,-0.001305,0.000332,0.000331,0.004119,-0.005831,0.000502,0.000503,0.000887,0.000888,0,-0.002137,0,0,-0.000185,0,0.000912,0,0.000011,0.000011,0.000332,0.000332,-0.000325,0,0.000607,0,0.00054,0.000539,0.000121,0,-0.001182,-0.001182,0.000803,0.000803,-0.001426,-0.001425,0.000467,0.000467,0.105113,0.105113,-0.104078,-0.104077,0,0.000176
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1
[M7] rank=7 service=ts-delivery-service metric=k8s.pod.cpu_limit_utilization baseline=0.001826 peak=0.043568 signed_z=146.144 onset_bin=58 onset_rel_s=437.27 persistence_bins=3
values_compact=delta:0.001541,0.00008,0.00008,0,-0.000062,0.000094,0.000095,0,-0.000022,-0.000023,-0.000182,0,0.000752,0,-0.000242,0,-0.00021,0,0.000181,0,-0.000261,-0.000261,0.000067,0.000066,0.000824,-0.001167,0.000101,0.0001,0.000178,0.000177,0,-0.000427,0,0,-0.000037,0,0.000182,0,0.000003,0.000002,0.000066,0.000067,-0.000065,0,0.000121,0,0.000108,0.000108,0.000024,0,-0.000236,-0.000237,0.000161,0.00016,-0.000285,-0.000285,0.000094,0.000093,0.021023,0.021022,-0.020815,-0.020816,0,0.000035
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1
[M8] rank=8 service=ts-delivery-service metric=container.cpu.usage baseline=0.009067 peak=0.199526 signed_z=130.417 onset_bin=58 onset_rel_s=437.27 persistence_bins=3
values_compact=delta:0.008026,0.00017,0.00017,-0.000992,0,0.00067,0.00067,0,0.001001,0,-0.001482,0,0.003744,0,-0.001554,0,-0.000081,0,-0.000551,-0.000552,0,-0.001188,-0.000051,-0.00005,0.003867,0,-0.004662,0,0.00074,0.000739,0,-0.000879,0,-0.000674,0.000218,0.000218,0.000061,0.000062,0,0.00067,0,0.001475,0,0,-0.000841,0.002374,0,0,-0.001658,-0.001999,0,0,0.001871,0,-0.001841,0,-0.000334,0,0.096085,0.096084,-0.095145,-0.095146,0.00056,0.00056
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1
[M9] rank=9 service=ts-user-service metric=hubble_http_request_duration_p95_seconds baseline=0.012253 peak=0.45 signed_z=116.279 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.00975,0,0.009625,-0.001875,-0.00775,0.00325,-0.003396,-0.00031,-0.000419,0.441125,-0.44525,0.004375,-0.000042
missing_mask_bits=0111011101110111011101110111011101110111111101110111011111111111
observed_counts_compact=rle:1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*7,1*1,0*3,1*1,0*3,1*1,0*11
[M10] rank=10 service=ts-ui-dashboard metric=hubble_http_request_duration_p90_seconds baseline=0.127921 peak=7.375 signed_z=113.007 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.147705,0.005457,-0.059829,0.1175,0.016667,-0.1325,-0.0475,0.000833,4.701667,-0.375,-4.28,4.655,2.625,-2.625,-4.515,-0.14
missing_mask_bits=1101110111011101110111011101110111011101110111011101110111011101
observed_counts_compact=csv:0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0
[M11] rank=11 service=ts-ui-dashboard metric=hubble_http_request_duration_p95_seconds baseline=0.19196 peak=7.4375 signed_z=109.309 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.237245,0.004317,-0.075312,0.07625,-0.00375,0,-0.165625,0.024375,4.7775,-0.1875,-4.59,4.7775,2.5625,-2.5625,-4.6325,-0.145
missing_mask_bits=1101110111011101110111011101110111011101110111011101111011101110
observed_counts_compact=csv:0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,0,1,0,0,0,1,0,0,0,1
[M12] rank=12 service=ts-security-service metric=k8s.pod.filesystem.usage baseline=515747.404255 peak=1105920.0 signed_z=45.197 onset_bin=33 onset_rel_s=250.402 persistence_bins=31
values_compact=delta:495616,0,0,4096,0,2048,2048,0,4096,0,0,0,4096,0,0,0,4096,0,4096,0,0,2048,2048,2048,2048,0,4096,0,4096,0,4096,0,0,28672,24576,18432,18432,20480,14336,14336,24576,20480,16384,20480,18432,22528,22528,22528,12288,20480,18432,2048,6144,18432,22528,10240,20480,24576,16384,16384,20480,16384,14336,18432
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[293.3138461112976,478.3807363510132]

=== LOG SUMMARY ===
{"entries":[{"error_logs":2671,"error_pct":100.0,"service":"ts-ui-dashboard","total_logs":2671},{"error_logs":726,"error_pct":16.0,"service":"ts-preserve-service","total_logs":4538},{"error_logs":145,"error_pct":15.92,"service":"ts-food-service","total_logs":911},{"error_logs":96,"error_pct":25.0,"service":"ts-delivery-service","total_logs":384},{"error_logs":95,"error_pct":25.0,"service":"ts-notification-service","total_logs":380},{"error_logs":14,"error_pct":0.42,"service":"ts-order-service","total_logs":3316}],"mode":"errors","omitted_services":24,"service_count":30}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":1180.0,"error_pct":10.1,"p95_during_ms":4420.7207161999995,"p95_pre_ms":345.35622699999976,"service":"ts-ui-dashboard","spans":2672},{"delta_pct":199.3,"error_pct":2.26,"p95_during_ms":962.5389395,"p95_pre_ms":321.60510375,"service":"loadgenerator","spans":2632},{"delta_pct":-82.9,"error_pct":60.02,"p95_during_ms":58.47337439999997,"p95_pre_ms":341.9456672999999,"service":"ts-preserve-service","spans":4167},{"delta_pct":-54.8,"error_pct":0.0,"p95_during_ms":15.431812899999995,"p95_pre_ms":34.108187,"service":"ts-consign-service","spans":296},{"delta_pct":49.4,"error_pct":0.0,"p95_during_ms":1015.0893007499991,"p95_pre_ms":679.594087,"service":"ts-route-plan-service","spans":651},{"delta_pct":-42.3,"error_pct":0.0,"p95_during_ms":3.479608999999998,"p95_pre_ms":6.034898149999992,"service":"ts-order-other-service","spans":6820},{"delta_pct":-30.3,"error_pct":0.0,"p95_during_ms":4.8014136,"p95_pre_ms":6.8850802,"service":"ts-user-service","spans":2250},{"delta_pct":-25.9,"error_pct":0.0,"p95_during_ms":3.3943910999999996,"p95_pre_ms":4.579106100000001,"service":"ts-verification-code-service","spans":1596}],"omitted_services":21,"service_count":29}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=35 omitted_edges=1
[{"evidence_source":"metric","onset_rel_s":276.0,"rank":1,"service":"ts-user-service","severity_z":116.279},{"evidence_source":"metric","onset_rel_s":291.0,"rank":2,"service":"ts-seat-service","severity_z":12.795},{"evidence_source":"trace","onset_rel_s":294.0,"rank":3,"service":"ts-ui-dashboard","severity_z":4.283},{"evidence_source":"trace","onset_rel_s":294.0,"rank":4,"service":"loadgenerator","severity_z":28.422},{"evidence_source":"metric","onset_rel_s":334.8,"rank":5,"service":"ts-contacts-service","severity_z":17.993},{"evidence_source":"metric","onset_rel_s":342.6,"rank":6,"service":"ts-food-service","severity_z":19.841},{"evidence_source":"metric","onset_rel_s":343.8,"rank":7,"service":"ts-security-service","severity_z":45.197},{"evidence_source":"metric","onset_rel_s":348.6,"rank":8,"service":"ts-preserve-service","severity_z":240.759},{"evidence_source":"metric","onset_rel_s":349.8,"rank":9,"service":"ts-news-service","severity_z":13.412},{"evidence_source":"metric","onset_rel_s":365.4,"rank":10,"service":"rabbitmq","severity_z":34.155},{"evidence_source":"metric","onset_rel_s":388.2,"rank":11,"service":"ts-voucher-service","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":435.0,"rank":12,"service":"ts-avatar-service","severity_z":10.574},{"evidence_source":"metric","onset_rel_s":439.8,"rank":13,"service":"ts-delivery-service","severity_z":146.144},{"evidence_source":"metric","onset_rel_s":447.0,"rank":14,"service":"ts-order-other-service","severity_z":168.555}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"ts-ui-dashboard","caller":"loadgenerator"},{"callee":"ts-contacts-service","caller":"ts-preserve-service"},{"callee":"ts-food-service","caller":"ts-preserve-service"},{"callee":"ts-seat-service","caller":"ts-preserve-service"},{"callee":"ts-security-service","caller":"ts-preserve-service"},{"callee":"ts-user-service","caller":"ts-preserve-service"},{"callee":"ts-order-other-service","caller":"ts-seat-service"},{"callee":"ts-order-other-service","caller":"ts-security-service"},{"callee":"ts-contacts-service","caller":"ts-ui-dashboard"},{"callee":"ts-food-service","caller":"ts-ui-dashboard"},{"callee":"ts-order-other-service","caller":"ts-ui-dashboard"},{"callee":"ts-preserve-service","caller":"ts-ui-dashboard"},{"callee":"ts-user-service","caller":"ts-ui-dashboard"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

[excluded before optimizer]

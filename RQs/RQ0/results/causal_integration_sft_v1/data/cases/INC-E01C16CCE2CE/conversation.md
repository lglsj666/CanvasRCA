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
opaque_id: INC-E01C16CCE2CE
observation_window={"duration_rel_s":479.681,"source_metric_rows":944}
selection_summary={"candidate_count":104,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":900,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["loadgenerator","loadgenerator-7c6465b994-k4j55","mysql","mysql-0","rabbitmq","rabbitmq-0","ts-admin-basic-info-service","ts-admin-basic-info-service-8498cf659d-xcftf","ts-admin-order-service","ts-admin-order-service-5f48c9847-g9825","ts-admin-route-service","ts-admin-route-service-67f9bbcd98-pk97f","ts-admin-travel-service","ts-admin-travel-service-7d676d8cf-xdgr6","ts-admin-user-service","ts-admin-user-service-5f875c8488-khvj6","ts-assurance-service","ts-assurance-service-6b6f9549bd-lvzn8","ts-auth-service","ts-auth-service-54bd57586c-55jxh","ts-avatar-service","ts-avatar-service-697c966bc9-gtdgd","ts-basic-service","ts-basic-service-599dcbcd59-2jm9m","ts-cancel-service","ts-cancel-service-5d6f598b75-ttlg2","ts-config-service","ts-config-service-788886954c-f5hbs","ts-consign-price-service","ts-consign-price-service-65d465fbbd-dmgzg","ts-consign-service","ts-consign-service-f89c85c6-x8fl8","ts-contacts-service","ts-contacts-service-746b87fbc6-528sd","ts-delivery-service","ts-delivery-service-669dcd76fc-w27gd","ts-execute-service","ts-execute-service-565f5cf898-7wf86","ts-food-delivery-service","ts-food-delivery-service-6fcc5f49db-nrnsj","ts-food-service","ts-food-service-5dd9757985-qpg6h","ts-gateway-service","ts-gateway-service-df699cb95-z9pws","ts-inside-payment-service","ts-inside-payment-service-69459cf8c4-9kpsz","ts-news-service","ts-news-service-6d6c6d7855-9fn4k","ts-notification-service","ts-notification-service-7967657c5d-pb5dz","ts-order-other-service","ts-order-other-service-86c75649c4-wk89p","ts-order-service","ts-order-service-554d59f5c-jf8tf","ts-payment-service","ts-payment-service-66bfbd95f5-qvtw6","ts-preserve-other-service","ts-preserve-other-service-6bbdcb9df4-zq8kp","ts-preserve-service","ts-preserve-service-87fbbf5b5-v6vnk","ts-price-service","ts-price-service-54b6b4b96-k5fw5","ts-rebook-service","ts-rebook-service-7f8fd67745-bswss","ts-route-plan-service","ts-route-plan-service-76fc6cc974-4ffrb","ts-route-service","ts-route-service-799f648896-vwf5q","ts-seat-service","ts-seat-service-675c89f44-hnzs5","ts-security-service","ts-security-service-6868bb5d87-4hp47","ts-station-food-service","ts-station-food-service-59fc9cbf74-g45z6","ts-station-service","ts-station-service-96ccf6fc-gpwgc","ts-ticket-office-service","ts-ticket-office-service-58c97df4b6-fd7h5","ts-train-food-service","ts-train-food-service-bcf66b6d8-6wk56","ts-train-service","ts-train-service-6bdbdb4547-8xwjx","ts-travel-plan-service","ts-travel-plan-service-5b7fb74b4f-frbzg","ts-travel-service","ts-travel-service-74794d67b9-k5pwr","ts-travel2-service","ts-travel2-service-6659b8fd5f-xj85n","ts-ui-dashboard","ts-ui-dashboard-59499f7b8b-v8dw9","ts-user-service","ts-user-service-87d8d9d54-dgxkt","ts-verification-code-service","ts-verification-code-service-6c9f97cb54-759cb","ts-voucher-service","ts-voucher-service-6f9ddf4fc4-l766j","ts-wait-order-service","ts-wait-order-service-bbf549d5-wmtmk","worker1","worker2","worker3","worker4","worker5","worker6"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[3.748,11.243,18.738,26.233,33.728,41.223,48.718,56.213,63.708,71.203,78.698,86.193,93.688,101.183,108.678,116.173,123.668,131.163,138.658,146.153,153.648,161.143,168.638,176.133,183.628,191.123,198.618,206.113,213.608,221.103,228.598,236.093,243.588,251.083,258.578,266.073,273.568,281.063,288.558,296.053,303.548,311.043,318.538,326.033,333.528,341.024,348.519,356.014,363.509,371.004,378.499,385.994,393.489,400.984,408.479,415.974,423.469,430.964,438.459,445.954,453.449,460.944,468.439,475.934]
[M1] rank=1 service=rabbitmq metric=container.memory.rss baseline=152126037.333333 peak=151638016.0 signed_z=-137.618 onset_bin=42 onset_rel_s=318.538 persistence_bins=22
values_compact=rle:152121344*10,152125440*7,152127488*1,152129536*22,152133632*2,152141824*13,152145920*3,151699456*3,151638016*2,151640064*1
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M2] rank=2 service=rabbitmq metric=k8s.pod.memory.rss baseline=152162560.0 peak=151674880.0 signed_z=-135.956 onset_bin=43 onset_rel_s=326.033 persistence_bins=21
values_compact=rle:152158208*11,152160256*1,152162304*7,152166400*22,152170496*2,152174592*1,152178688*9,152182784*6,151928832*1,151674880*3,151676928*1
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M3] rank=3 service=ts-consign-price-service metric=container.cpu.usage baseline=0.007071 peak=0.237168 signed_z=131.154 onset_bin=35 onset_rel_s=266.073 persistence_bins=2
values_compact=delta:0.005495,0.001328,0,-0.000248,0,-0.000079,0,0.003093,0,-0.003527,0,0.000502,0.000503,0.002467,0.002467,-0.002148,-0.002149,0.000203,0.000202,-0.000153,0,-0.000823,-0.000822,0.000344,0.000344,0,-0.002233,0,0,-0.000069,0,0.001691,-0.001686,0.000349,0.000348,0.115885,0.115884,-0.230324,0,0.000131,0,-0.000355,-0.000354,0.000284,0,-0.000455,-0.000455,0.000563,0.000563,0,-0.000773,0,-0.000461,0,0.000786,0,0,-0.001395,-0.000498,0,0.00016,0,0,0.000554
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M4] rank=4 service=ts-train-food-service metric=container.cpu.usage baseline=0.022083 peak=0.73113 signed_z=108.582 onset_bin=39 onset_rel_s=296.053 persistence_bins=2
values_compact=delta:0.022344,0,0.002223,0.016174,0,-0.023004,0,0.005481,0,-0.011324,0.006554,0.006554,0.001268,0.001268,-0.001695,-0.004473,0,0,0.00217,-0.01203,0,0.003935,0.003524,0.003524,-0.005484,0,0.001545,0.001545,0.00381,0.003811,-0.005582,0,-0.003216,-0.003217,0,-0.011396,0,0.000294,0,0.726527,0,-0.726585,0,0,0.00049,-0.000809,0,0.000893,0,-0.001136,0,0,0.000405,-0.001042,0,0.000784,-0.000227,-0.000227,0,0.000133,0,0,0.00086,0
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1
[M5] rank=5 service=ts-train-food-service metric=k8s.pod.cpu.node.utilization baseline=0.000174 peak=0.005673 signed_z=104.87 onset_bin=38 onset_rel_s=288.558 persistence_bins=3
values_compact=delta:0.000202,0,-0.000043,0.000155,0,-0.00018,0,0,0.000038,-0.00007,0,0.000123,0,-0.000025,0,-0.000029,0,-0.000024,0.000013,0.000014,-0.000031,-0.000031,0.000038,0.000038,-0.000067,0,0.000017,0.000018,0.000084,0,-0.000076,0,-0.000018,0,-0.000108,0,-0.000002,-0.000001,0.002819,0.002819,0,-0.005633,-0.000002,-0.000002,0,0.000001,0,0.000001,0,0,-0.000008,0,0.000004,0,-0.000001,-0.000001,-0.000002,-0.000002,0,0.000002,0.000003,0.000003,0.000001,0.000001
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1
[M6] rank=6 service=ts-train-food-service metric=k8s.pod.cpu.usage baseline=0.022324 peak=0.726187 signed_z=104.87 onset_bin=38 onset_rel_s=288.558 persistence_bins=3
values_compact=delta:0.025848,0,-0.005481,0.019801,0,-0.023065,0,0,0.004899,-0.008984,0,0.015763,0,-0.003203,0,-0.00369,0,-0.003113,0.001727,0.001727,-0.003924,-0.003924,0.004853,0.004853,-0.008615,0,0.002227,0.002228,0.010779,0,-0.009656,0,-0.002334,0,-0.013897,0,-0.000157,-0.000157,0.360841,0.360841,0,-0.721003,-0.000316,-0.000316,0.000096,0.000096,0,0.00014,0,0,-0.000994,0,0.000424,0,-0.000141,-0.000141,-0.000213,-0.000214,0,0.000244,0.00035,0.000349,0.000177,0.000177
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1
[M7] rank=7 service=ts-train-food-service metric=k8s.pod.cpu_limit_utilization baseline=0.004465 peak=0.145237 signed_z=104.87 onset_bin=38 onset_rel_s=288.558 persistence_bins=3
values_compact=delta:0.00517,0,-0.001097,0.003961,0,-0.004613,0,0,0.000979,-0.001796,0,0.003152,0,-0.00064,0,-0.000738,0,-0.000623,0.000345,0.000346,-0.000785,-0.000785,0.000971,0.00097,-0.001723,0,0.000446,0.000445,0.002156,0,-0.001931,0,-0.000467,0,-0.002779,0,-0.000032,-0.000031,0.072168,0.072168,0,-0.1442,-0.000063,-0.000064,0.00002,0.000019,0,0.000028,0,0,-0.000199,0,0.000085,0,-0.000028,-0.000029,-0.000042,-0.000043,0,0.000049,0.00007,0.00007,0.000035,0.000035
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1
[M8] rank=8 service=ts-consign-price-service metric=k8s.pod.cpu.node.utilization baseline=5.5e-05 peak=0.00124 signed_z=78.949 onset_bin=35 onset_rel_s=266.073 persistence_bins=3
values_compact=delta:0.000043,0,0.000019,0,0,-0.000027,0,0.000048,0,-0.000017,-0.000017,0.000003,0.000003,0.000013,0.000013,-0.000006,-0.000007,-0.000002,-0.000002,-0.000004,-0.000004,-0.000007,0,0.00001,0,-0.000019,0,-0.000001,0,-0.000003,-0.000002,0.000016,0,-0.000011,0,0.000601,0.0006,0,-0.001185,0,-0.000005,0,0,-0.000002,0,-0.000001,0,0.000005,0,-0.000002,-0.000002,-0.000001,-0.000001,0.000002,0.000001,0,-0.000009,0,-0.000004,0,0,-0.000001,0.000006,-0.000002
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M9] rank=9 service=ts-consign-price-service metric=k8s.pod.cpu.usage baseline=0.007053 peak=0.158732 signed_z=78.949 onset_bin=35 onset_rel_s=266.073 persistence_bins=3
values_compact=delta:0.005472,0,0.002468,0,0,-0.003522,0,0.006219,0,-0.002159,-0.002159,0.000389,0.000388,0.001653,0.001652,-0.000832,-0.000832,-0.000302,-0.000303,-0.000457,-0.000458,-0.000948,0,0.001288,0,-0.002449,0,-0.000081,-0.000081,-0.000312,-0.000312,0.002016,0,-0.001312,0,0.076853,0.076853,0,-0.15169,0,-0.000626,0,0,-0.000209,0,-0.000213,0,0.000721,0,-0.000312,-0.000312,-0.0001,-0.0001,0.000218,0.000219,0,-0.001203,0,-0.000552,0,0,-0.000032,0.000701,-0.000224
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M10] rank=10 service=ts-consign-price-service metric=k8s.pod.cpu_limit_utilization baseline=0.001411 peak=0.031746 signed_z=78.949 onset_bin=35 onset_rel_s=266.073 persistence_bins=3
values_compact=delta:0.001094,0,0.000494,0,0,-0.000704,0,0.001243,0,-0.000431,-0.000432,0.000078,0.000077,0.000331,0.00033,-0.000166,-0.000167,-0.00006,-0.000061,-0.000091,-0.000092,-0.000189,0,0.000257,0,-0.000489,0,-0.000017,-0.000016,-0.000062,-0.000063,0.000404,0,-0.000263,0,0.015371,0.01537,0,-0.030338,0,-0.000125,0,0,-0.000042,0,-0.000042,0,0.000144,0,-0.000062,-0.000063,-0.00002,-0.00002,0.000044,0.000044,0,-0.000241,0,-0.00011,0,0,-0.000007,0.00014,-0.000044
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M11] rank=11 service=ts-consign-price-service metric=container.memory.rss baseline=734764458.666667 peak=737423360.0 signed_z=65.532 onset_bin=35 onset_rel_s=266.073 persistence_bins=29
values_compact=delta:734699520,20480,0,4096,0,12288,0,61440,0,0,0,0,0,-22528,-22528,36864,36864,0,0,0,0,-36864,-36864,-14336,-14336,0,0,0,0,16384,0,12288,0,0,0,1255424,1255424,0,0,16384,0,0,0,0,0,0,0,2048,2048,0,0,0,0,0,139264,0,0,0,0,0,0,0,0,-131072
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M12] rank=12 service=ts-consign-price-service metric=k8s.pod.memory.rss baseline=734800384.0 peak=737460224.0 signed_z=58.173 onset_bin=35 onset_rel_s=266.073 persistence_bins=29
values_compact=delta:734736384,0,24576,0,0,0,0,73728,0,0,0,0,0,-43008,-43008,57344,57344,0,0,0,0,0,0,-102400,0,0,0,8192,8192,0,0,12288,0,0,0,1255424,1255424,0,16384,0,0,0,0,0,0,0,0,4096,0,0,0,0,0,36864,36864,0,65536,0,0,0,0,0,-131072,0
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[433.1362683773041,478.08232831954956]

=== LOG SUMMARY ===
{"entries":[{"error_logs":2650,"error_pct":19.26,"service":"ts-seat-service","total_logs":13758},{"error_logs":287,"error_pct":16.85,"service":"ts-food-service","total_logs":1703},{"error_logs":99,"error_pct":5.85,"service":"ts-preserve-service","total_logs":1692},{"error_logs":99,"error_pct":2.02,"service":"ts-order-service","total_logs":4898},{"error_logs":96,"error_pct":25.0,"service":"ts-delivery-service","total_logs":384},{"error_logs":96,"error_pct":25.0,"service":"ts-notification-service","total_logs":384},{"error_logs":11,"error_pct":0.33,"service":"ts-travel2-service","total_logs":3313},{"error_logs":8,"error_pct":0.73,"service":"ts-travel-plan-service","total_logs":1101}],"mode":"errors","omitted_services":23,"service_count":31}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":21213.3,"error_pct":0.0,"p95_during_ms":25392.669566,"p95_pre_ms":119.13985329999988,"service":"ts-travel2-service","spans":4845},{"delta_pct":3465.9,"error_pct":0.0,"p95_during_ms":29974.513272300002,"p95_pre_ms":840.5881821500044,"service":"ts-route-plan-service","spans":1509},{"delta_pct":2904.3,"error_pct":0.0,"p95_during_ms":30090.169372,"p95_pre_ms":1001.585591,"service":"ts-travel-plan-service","spans":1961},{"delta_pct":-71.2,"error_pct":0.0,"p95_during_ms":3.2904885,"p95_pre_ms":11.437511199999998,"service":"ts-assurance-service","spans":534},{"delta_pct":-63.8,"error_pct":0.0,"p95_during_ms":8.044785649999998,"p95_pre_ms":22.200792599999915,"service":"ts-consign-service","spans":535},{"delta_pct":-56.0,"error_pct":0.0,"p95_during_ms":4.0965320499999995,"p95_pre_ms":9.300149899999994,"service":"ts-train-food-service","spans":2076},{"delta_pct":-51.9,"error_pct":0.0,"p95_during_ms":11.632529199999999,"p95_pre_ms":24.160364699999995,"service":"ts-seat-service","spans":10981},{"delta_pct":-44.7,"error_pct":0.0,"p95_during_ms":309.51225799999975,"p95_pre_ms":560.1885002500001,"service":"ts-preserve-service","spans":1100}],"omitted_services":22,"service_count":30}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=35 omitted_edges=0
[{"evidence_source":"metric","onset_rel_s":268.2,"rank":1,"service":"ts-consign-price-service","severity_z":131.154},{"evidence_source":"metric","onset_rel_s":291.6,"rank":2,"service":"ts-seat-service","severity_z":10.226},{"evidence_source":"metric","onset_rel_s":297.0,"rank":3,"service":"ts-train-food-service","severity_z":108.582},{"evidence_source":"metric","onset_rel_s":340.8,"rank":4,"service":"mysql","severity_z":11.135},{"evidence_source":"metric","onset_rel_s":411.0,"rank":5,"service":"ts-avatar-service","severity_z":18.023},{"evidence_source":"metric","onset_rel_s":438.0,"rank":6,"service":"rabbitmq","severity_z":137.618},{"evidence_source":"trace","onset_rel_s":444.6,"rank":7,"service":"ts-route-service","severity_z":10.372},{"evidence_source":"none","onset_rel_s":null,"rank":8,"service":"ts-preserve-service","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":9,"service":"ts-wait-order-service","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":10,"service":"ts-news-service","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":11,"service":"ts-admin-order-service","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":12,"service":"ts-gateway-service","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":13,"service":"ts-admin-travel-service","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":14,"service":"ts-order-service","severity_z":0.0}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"ts-order-service","caller":"ts-preserve-service"},{"callee":"ts-seat-service","caller":"ts-preserve-service"},{"callee":"ts-order-service","caller":"ts-seat-service"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

[excluded before optimizer]

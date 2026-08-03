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
opaque_id: INC-2E446C3FE621
observation_window={"duration_rel_s":479.323,"source_metric_rows":948}
selection_summary={"candidate_count":105,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":902,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["loadgenerator","loadgenerator-7c87799cd5-qbxj8","mysql","mysql-0","rabbitmq","rabbitmq-0","ts-admin-basic-info-service","ts-admin-basic-info-service-8498cf659d-lwnl5","ts-admin-order-service","ts-admin-order-service-5f48c9847-bznln","ts-admin-route-service","ts-admin-route-service-67f9bbcd98-jjfl8","ts-admin-travel-service","ts-admin-travel-service-7d676d8cf-76v2r","ts-admin-user-service","ts-admin-user-service-5f875c8488-g9vzg","ts-assurance-service","ts-assurance-service-6b6f9549bd-hjqzg","ts-auth-service","ts-auth-service-54bd57586c-wmc5g","ts-avatar-service","ts-avatar-service-697c966bc9-l6sqj","ts-basic-service","ts-basic-service-599dcbcd59-2wjhj","ts-cancel-service","ts-cancel-service-5d6f598b75-lx9ql","ts-config-service","ts-config-service-788886954c-5nv9g","ts-consign-price-service","ts-consign-price-service-65d465fbbd-znsrp","ts-consign-service","ts-consign-service-f89c85c6-nfldf","ts-contacts-service","ts-contacts-service-746b87fbc6-xrr8s","ts-delivery-service","ts-delivery-service-669dcd76fc-rg99h","ts-execute-service","ts-execute-service-565f5cf898-f7bng","ts-food-delivery-service","ts-food-delivery-service-6fcc5f49db-t6gb6","ts-food-service","ts-food-service-5dd9757985-7vfpl","ts-gateway-service","ts-gateway-service-df699cb95-94j2g","ts-inside-payment-service","ts-inside-payment-service-69459cf8c4-82kgj","ts-news-service","ts-news-service-6d6c6d7855-t64f9","ts-notification-service","ts-notification-service-7967657c5d-wgv7s","ts-order-other-service","ts-order-other-service-86c75649c4-lgsnc","ts-order-service","ts-order-service-554d59f5c-s9x6h","ts-payment-service","ts-payment-service-66bfbd95f5-rtjzx","ts-preserve-other-service","ts-preserve-other-service-6bbdcb9df4-8cjjn","ts-preserve-service","ts-preserve-service-87fbbf5b5-4828k","ts-price-service","ts-price-service-54b6b4b96-8pcsx","ts-rebook-service","ts-rebook-service-7f8fd67745-htq66","ts-route-plan-service","ts-route-plan-service-76fc6cc974-nf2g9","ts-route-service","ts-route-service-799f648896-l29hr","ts-seat-service","ts-seat-service-675c89f44-t26lb","ts-security-service","ts-security-service-6868bb5d87-pqtwn","ts-station-food-service","ts-station-food-service-59fc9cbf74-kcm8f","ts-station-service","ts-station-service-96ccf6fc-llxm9","ts-ticket-office-service","ts-ticket-office-service-58c97df4b6-8m4fh","ts-train-food-service","ts-train-food-service-bcf66b6d8-b4r64","ts-train-service","ts-train-service-6bdbdb4547-qghxc","ts-travel-plan-service","ts-travel-plan-service-5b7fb74b4f-mxjp7","ts-travel-service","ts-travel-service-74794d67b9-9f7xs","ts-travel2-service","ts-travel2-service-6659b8fd5f-59l5c","ts-ui-dashboard","ts-ui-dashboard-59499f7b8b-sxb6z","ts-user-service","ts-user-service-87d8d9d54-n6tmc","ts-user-service-87d8d9d54-vswdv","ts-verification-code-service","ts-verification-code-service-6c9f97cb54-95v7n","ts-voucher-service","ts-voucher-service-6f9ddf4fc4-llzln","ts-wait-order-service","ts-wait-order-service-bbf549d5-mzd4z","worker1","worker2","worker3","worker4","worker5","worker6"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[3.745,11.234,18.724,26.213,33.702,41.192,48.681,56.171,63.66,71.149,78.639,86.128,93.618,101.107,108.597,116.086,123.575,131.065,138.554,146.044,153.533,161.022,168.512,176.001,183.491,190.98,198.47,205.959,213.448,220.938,228.427,235.917,243.406,250.895,258.385,265.874,273.364,280.853,288.343,295.832,303.321,310.811,318.3,325.79,333.279,340.768,348.258,355.747,363.237,370.726,378.216,385.705,393.194,400.684,408.173,415.663,423.152,430.641,438.131,445.62,453.11,460.599,468.089,475.578]
[M1] rank=1 service=ts-ticket-office-service metric=k8s.pod.memory.node.utilization baseline=0.000694 peak=0.000694 signed_z=999.0 onset_bin=0 onset_rel_s=3.745 persistence_bins=64
values_compact=rle:0.000694*64
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M2] rank=2 service=ts-user-service metric=container.filesystem.usage baseline=466944.0 peak=0.0 signed_z=-999.0 onset_bin=32 onset_rel_s=243.406 persistence_bins=6
values_compact=rle:466944*32,233472*1,0*1,69632*1,442368*3,466944*26
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1
[M3] rank=3 service=ts-user-service metric=k8s.pod.memory.node.utilization baseline=0.005907 peak=0.0 signed_z=-140.16 onset_bin=32 onset_rel_s=243.406 persistence_bins=20
values_compact=delta:0.005866,0,0,0,0.000001,0,0,0,0.000011,0,-0.000005,0,0,0,0,0,0.000001,0.000001,0.00004,0.00004,0,0,0,0,0,0,0.000001,0.000002,-0.000002,0.000002,-0.000001,0,-0.002979,-0.002978,0.001044,0.001044,0.001999,0,0.001202,0,0.000617,0,0.00002,0.000021,-0.000016,-0.000016,0,0.000025,0.000003,0.000004,0.000038,0.000038,0.000012,0.000013,0.000035,0.000036,-0.00004,0.000008,0,0.000017,0,0.000036,0,0.000012
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1
[M4] rank=4 service=ts-user-service metric=k8s.pod.memory.usage baseline=797656544.653061 peak=0.0 signed_z=-140.16 onset_bin=32 onset_rel_s=243.406 persistence_bins=20
values_compact=delta:792076288,0,2048,2048,102400,0,61440,0,1503232,0,-757760,0,12288,0,18432,18432,98304,98304,5406720,5406720,0,0,34816,34816,10240,10240,161792,161792,-258048,270336,-65536,-65536,-402171904,-402171904,140961792,140961792,269979648,0,162324480,0,83218432,0,2787328,2787328,-2160640,-2160640,0,3354624,462848,462848,5150720,5150720,1671168,1671168,4784128,4784128,-5357568,1114112,0,2244608,0,4849664,0,1642496
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1
[M5] rank=5 service=ts-user-service metric=k8s.pod.memory_limit_utilization baseline=0.247625 peak=0.0 signed_z=-140.16 onset_bin=32 onset_rel_s=243.406 persistence_bins=20
values_compact=delta:0.245893,0,0,0.000001,0.000032,0,0.000019,0,0.000467,0,-0.000236,0,0.000004,0,0.000006,0.000006,0.00003,0.000031,0.001678,0.001679,0,0,0.00001,0.000011,0.000003,0.000004,0.00005,0.00005,-0.00008,0.000084,-0.00002,-0.000021,-0.12485,-0.124851,0.04376,0.043761,0.083812,0,0.050392,0,0.025835,0,0.000865,0.000865,-0.00067,-0.000671,0,0.001041,0.000144,0.000144,0.001599,0.001599,0.000519,0.000518,0.001486,0.001485,-0.001663,0.000345,0,0.000697,0,0.001506,0,0.00051
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1
[M6] rank=6 service=ts-user-service metric=k8s.pod.memory.available baseline=2423953951.346939 peak=3221225472.0 signed_z=140.093 onset_bin=32 onset_rel_s=243.406 persistence_bins=20
values_compact=delta:2429534208,0,-2048,-2048,-102400,0,-61440,0,-1503232,0,757760,0,-12288,0,-18432,-18432,-98304,-98304,-5406720,-5406720,0,0,-34816,-34816,-10240,-10240,-161792,-161792,258048,-270336,65536,65536,401979392,401979392,-140945408,-140945408,-269627392,0,-162324480,0,-83218432,0,-2787328,-2787328,2160640,2160640,0,-3354624,-462848,-462848,-5150720,-5150720,-1671168,-1671168,-4784128,-4784128,5357568,-1114112,0,-2244608,0,-4849664,0,-1642496
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1
[M7] rank=7 service=ts-user-service metric=k8s.pod.memory.working_set baseline=797271520.653061 peak=0.0 signed_z=-140.093 onset_bin=32 onset_rel_s=243.406 persistence_bins=20
values_compact=delta:791691264,0,2048,2048,102400,0,61440,0,1503232,0,-757760,0,12288,0,18432,18432,98304,98304,5406720,5406720,0,0,34816,34816,10240,10240,161792,161792,-258048,270336,-65536,-65536,-401979392,-401979392,140945408,140945408,269627392,0,162324480,0,83218432,0,2787328,2787328,-2160640,-2160640,0,3354624,462848,462848,5150720,5150720,1671168,1671168,4784128,4784128,-5357568,1114112,0,2244608,0,4849664,0,1642496
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1
[M8] rank=8 service=ts-user-service metric=k8s.pod.memory.rss baseline=785763098.122449 peak=0.0 signed_z=-139.428 onset_bin=32 onset_rel_s=243.406 persistence_bins=20
values_compact=delta:780308480,0,0,0,110592,0,61440,0,733184,0,8192,0,8192,0,22528,22528,96256,96256,5263360,5263360,0,0,40960,40960,135168,135168,34816,34816,0,0,67584,67584,-396275712,-396275712,136728576,136728576,260149248,0,159264768,0,92106752,0,2373632,2373632,-1406976,-1406976,0,3141632,567296,567296,5142528,5142528,1277952,1277952,4843520,4843520,-4685824,331776,0,1802240,0,5791744,0,1912832
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1
[M9] rank=9 service=ts-user-service metric=container.memory.working_set baseline=796320579.918367 peak=211255296.0 signed_z=-103.404 onset_bin=32 onset_rel_s=243.406 persistence_bins=19
values_compact=delta:791011328,0,-8192,0,114688,65536,0,630784,0,110592,4096,4096,0,28672,0,65536,0,147456,0,10547200,131072,131072,65536,0,-81920,0,135168,0,565248,0,-520192,0,-295946240,-255469568,32741376,3262464,169340928,169340928,0,170700800,-2955264,-2955264,1904640,1904640,2396160,0,2224128,0,2211840,0,10452992,0,2449408,0,5056512,5056512,-2521088,-2521088,0,3158016,2689024,2689024,866304,866304
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1
[M10] rank=10 service=ts-user-service metric=container.memory.rss baseline=785492929.306122 peak=279183360.0 signed_z=-90.6 onset_bin=34 onset_rel_s=258.385 persistence_bins=15
values_compact=delta:780267520,0,0,0,110592,61440,0,364544,0,376832,4096,4096,0,28672,0,61440,0,147456,0,10526720,0,0,69632,0,204800,0,98304,0,49152,0,0,0,0,-513191936,0,160000000,160000000,0,175902720,2609152,2609152,1890304,1890304,2314240,0,2478080,0,2203648,0,10416128,0,679936,0,5750784,5750784,-2316288,-2316288,0,1875968,2932736,2932736,1021952,1021952
missing_mask_bits=0000000000000000000000000000000001000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,0,1,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1
[M11] rank=11 service=ts-user-service metric=container.memory.available baseline=2424904892.081633 peak=2933489664.0 signed_z=89.887 onset_bin=34 onset_rel_s=258.385 persistence_bins=17
values_compact=delta:2430214144,0,8192,0,-114688,-65536,0,-630784,0,-110592,-4096,-4096,0,-28672,0,-65536,0,-147456,0,-10547200,-131072,-131072,-65536,0,81920,0,-135168,0,-565248,0,520192,0,0,515411968,0,-169340928,-169340928,0,-170700800,2955264,2955264,-1904640,-1904640,-2396160,0,-2224128,0,-2211840,0,-10452992,0,-2449408,0,-5056512,-5056512,2521088,2521088,0,-3158016,-2689024,-2689024,-866304,-866304
missing_mask_bits=0000000000000000000000000000000001000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,0,1,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1
[M12] rank=12 service=ts-user-service metric=container.memory.usage baseline=796705603.918367 peak=288120832.0 signed_z=-89.887 onset_bin=34 onset_rel_s=258.385 persistence_bins=17
values_compact=delta:791396352,0,-8192,0,114688,65536,0,630784,0,110592,4096,4096,0,28672,0,65536,0,147456,0,10547200,131072,131072,65536,0,-81920,0,135168,0,565248,0,-520192,0,0,-515411968,0,169340928,169340928,0,170700800,-2955264,-2955264,1904640,1904640,2396160,0,2224128,0,2211840,0,10452992,0,2449408,0,5056512,5056512,-2521088,-2521088,0,3158016,2689024,2689024,866304,866304
missing_mask_bits=0000000000000000000000000000000001000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,0,1,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[298.89798045158386,478.9173996448517]

=== LOG SUMMARY ===
{"entries":[{"error_logs":4490,"error_pct":19.31,"service":"ts-seat-service","total_logs":23249},{"error_logs":460,"error_pct":16.92,"service":"ts-food-service","total_logs":2718},{"error_logs":154,"error_pct":5.83,"service":"ts-preserve-service","total_logs":2641},{"error_logs":154,"error_pct":1.88,"service":"ts-order-service","total_logs":8178},{"error_logs":96,"error_pct":25.0,"service":"ts-delivery-service","total_logs":384},{"error_logs":96,"error_pct":25.0,"service":"ts-notification-service","total_logs":384},{"error_logs":5,"error_pct":0.3,"service":"ts-user-service","total_logs":1693},{"error_logs":2,"error_pct":2.22,"service":"ts-inside-payment-service","total_logs":90}],"mode":"errors","omitted_services":22,"service_count":30}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":-63.5,"error_pct":0.0,"p95_during_ms":594.8579051999993,"p95_pre_ms":1627.826109999999,"service":"ts-travel-plan-service","spans":3254},{"delta_pct":-63.0,"error_pct":0.0,"p95_during_ms":11.460573599999998,"p95_pre_ms":30.9347565,"service":"ts-consign-service","spans":1063},{"delta_pct":-62.1,"error_pct":0.0,"p95_during_ms":442.50349739999854,"p95_pre_ms":1167.8376585,"service":"ts-route-plan-service","spans":2394},{"delta_pct":-49.0,"error_pct":0.0,"p95_during_ms":292.0190417999985,"p95_pre_ms":572.6206669999998,"service":"ts-preserve-service","spans":1716},{"delta_pct":-43.7,"error_pct":0.0,"p95_during_ms":49.027829749999995,"p95_pre_ms":87.04741879999999,"service":"ts-cancel-service","spans":27},{"delta_pct":-42.0,"error_pct":0.0,"p95_during_ms":11.732990049999998,"p95_pre_ms":20.214420399999998,"service":"ts-consign-price-service","spans":95},{"delta_pct":-40.7,"error_pct":0.0,"p95_during_ms":5.021324399999999,"p95_pre_ms":8.474115199999996,"service":"ts-train-food-service","spans":3310},{"delta_pct":-38.3,"error_pct":0.0,"p95_during_ms":21.9380938,"p95_pre_ms":35.55373284999998,"service":"ts-security-service","spans":1980}],"omitted_services":22,"service_count":30}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=35 omitted_edges=0
[{"evidence_source":"metric","onset_rel_s":244.8,"rank":1,"service":"ts-user-service","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":301.2,"rank":2,"service":"mysql","severity_z":15.803},{"evidence_source":"metric","onset_rel_s":304.2,"rank":3,"service":"ts-ticket-office-service","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":331.2,"rank":4,"service":"ts-seat-service","severity_z":12.783},{"evidence_source":"metric","onset_rel_s":336.0,"rank":5,"service":"ts-contacts-service","severity_z":12.136},{"evidence_source":"metric","onset_rel_s":354.0,"rank":6,"service":"ts-config-service","severity_z":30.466},{"evidence_source":"metric","onset_rel_s":391.2,"rank":7,"service":"loadgenerator","severity_z":47.794},{"evidence_source":"metric","onset_rel_s":405.0,"rank":8,"service":"ts-avatar-service","severity_z":12.19},{"evidence_source":"metric","onset_rel_s":409.2,"rank":9,"service":"ts-cancel-service","severity_z":74.062},{"evidence_source":"metric","onset_rel_s":431.4,"rank":10,"service":"ts-preserve-service","severity_z":26.973},{"evidence_source":"metric","onset_rel_s":436.2,"rank":11,"service":"rabbitmq","severity_z":14.161},{"evidence_source":"metric","onset_rel_s":439.8,"rank":12,"service":"ts-security-service","severity_z":18.991},{"evidence_source":"metric","onset_rel_s":444.0,"rank":13,"service":"ts-consign-service","severity_z":27.256},{"evidence_source":"metric","onset_rel_s":460.2,"rank":14,"service":"ts-gateway-service","severity_z":47.21}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"ts-user-service","caller":"ts-cancel-service"},{"callee":"ts-contacts-service","caller":"ts-preserve-service"},{"callee":"ts-seat-service","caller":"ts-preserve-service"},{"callee":"ts-security-service","caller":"ts-preserve-service"},{"callee":"ts-user-service","caller":"ts-preserve-service"},{"callee":"ts-config-service","caller":"ts-seat-service"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

{"confidence":"high","reason":"Rank ts-user-service first because ts-user-service has direct container.filesystem.usage evidence (signed-z -999, persistence 6 bins); although ts-cancel-service is salient, the caller path ts-cancel-service -> ts-user-service means a disturbance in the callee can propagate back toward that caller-side symptom.","services":["ts-user-service","ts-cancel-service"]}

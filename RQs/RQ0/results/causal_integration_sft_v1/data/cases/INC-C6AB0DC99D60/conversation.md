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
opaque_id: INC-C6AB0DC99D60
observation_window={"duration_rel_s":478.352,"source_metric_rows":951}
selection_summary={"candidate_count":104,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":901,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["loadgenerator","loadgenerator-d75cc479f-cf5m8","mysql","mysql-0","rabbitmq","rabbitmq-0","ts-admin-basic-info-service","ts-admin-basic-info-service-66cdcc94bc-rkbpg","ts-admin-order-service","ts-admin-order-service-5b6dc77d7d-zkdmd","ts-admin-route-service","ts-admin-route-service-f9c84f85f-ffbfl","ts-admin-travel-service","ts-admin-travel-service-659b5c9df4-p6j42","ts-admin-user-service","ts-admin-user-service-5bfc8844b9-82m5v","ts-assurance-service","ts-assurance-service-75c854dc5c-r9tlx","ts-auth-service","ts-auth-service-69bdd5df8-5xffs","ts-avatar-service","ts-avatar-service-845b64df6-qxdj2","ts-basic-service","ts-basic-service-7c6d59d5c4-rnvz8","ts-cancel-service","ts-cancel-service-7ffd988fdb-2b8rj","ts-config-service","ts-config-service-55cffbf48b-xnrql","ts-consign-price-service","ts-consign-price-service-654cb4fc65-6hjrd","ts-consign-service","ts-consign-service-9954fddf-nm97w","ts-contacts-service","ts-contacts-service-6d745b6c8f-dpv6x","ts-delivery-service","ts-delivery-service-694895c6cb-77h5m","ts-execute-service","ts-execute-service-8457c56cb7-njp9f","ts-food-delivery-service","ts-food-delivery-service-96d856899-xfmxj","ts-food-service","ts-food-service-64d454885b-fbz6g","ts-gateway-service","ts-gateway-service-7f988fb8c4-j9zk5","ts-inside-payment-service","ts-inside-payment-service-5ccb8ccb87-6smbp","ts-news-service","ts-news-service-6d6c6d7855-9nsjr","ts-notification-service","ts-notification-service-58f6c468d7-v925s","ts-order-other-service","ts-order-other-service-5d6878687f-tsdlc","ts-order-service","ts-order-service-6794d6f564-9gdm9","ts-payment-service","ts-payment-service-58854d694-fh9x6","ts-preserve-other-service","ts-preserve-other-service-64fd9c88cf-mhq8b","ts-preserve-service","ts-preserve-service-696df489d4-xzld9","ts-price-service","ts-price-service-67c895b45-pznbl","ts-rebook-service","ts-rebook-service-7c7644bbdd-tlprs","ts-route-plan-service","ts-route-plan-service-556cddc5c9-wk5nk","ts-route-service","ts-route-service-cfc6dbcf7-7rg95","ts-seat-service","ts-seat-service-6c78b7d797-7slwd","ts-security-service","ts-security-service-55f5b777bb-6qttj","ts-station-food-service","ts-station-food-service-746f6779d7-fls6w","ts-station-service","ts-station-service-65986cc944-v7bdb","ts-ticket-office-service","ts-ticket-office-service-d7c58b8c7-lkbwk","ts-train-food-service","ts-train-food-service-d5485c677-fd7gt","ts-train-service","ts-train-service-9b56d75b6-w7f2q","ts-travel-plan-service","ts-travel-plan-service-7875c49896-h5z8c","ts-travel-service","ts-travel-service-c7b5c6d9b-2822r","ts-travel2-service","ts-travel2-service-7ff5bbbf54-v8mxz","ts-ui-dashboard","ts-ui-dashboard-57867cb85c-pj6hs","ts-user-service","ts-user-service-54dd6b48c-2746k","ts-verification-code-service","ts-verification-code-service-85785c4f79-669v8","ts-voucher-service","ts-voucher-service-689c4fc885-5mmvp","ts-wait-order-service","ts-wait-order-service-7cf6bc9468-p6sbl","worker1","worker2","worker3","worker4","worker5","worker6"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[3.737,11.211,18.686,26.16,33.634,41.108,48.583,56.057,63.531,71.005,78.48,85.954,93.428,100.902,108.377,115.851,123.325,130.799,138.273,145.748,153.222,160.696,168.17,175.645,183.119,190.593,198.067,205.542,213.016,220.49,227.964,235.439,242.913,250.387,257.861,265.336,272.81,280.284,287.758,295.233,302.707,310.181,317.655,325.13,332.604,340.078,347.552,355.027,362.501,369.975,377.449,384.924,392.398,399.872,407.346,414.82,422.295,429.769,437.243,444.717,452.192,459.666,467.14,474.614]
[M1] rank=1 service=ts-cancel-service metric=k8s.pod.cpu.node.utilization baseline=5.7e-05 peak=0.001763 signed_z=83.558 onset_bin=42 onset_rel_s=317.655 persistence_bins=3
values_compact=rle:0.000085*1,0.000048*1,0.000047*2,0.000052*1,0.000057*1,0.000039*2,0.0001*2,0.000071*1,0.000041*3,0.000065*1,0.000089*1,0.000064*1,0.00004*2,0.000043*2,0.00006*4,0.000053*3,0.000056*1,0.000053*2,0.00005*2,0.000048*2,0.000041*2,0.000052*3,0.000035*2,0.001763*2,0.000906*1,0.00005*1,0.000038*2,0.000039*2,0.000046*2,0.00005*2,0.000033*2,0.000035*2,0.000047*2,0.000034*2,0.00004*1,0.000035*1
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,1,2
[M2] rank=2 service=ts-cancel-service metric=k8s.pod.cpu.usage baseline=0.007278 peak=0.225617 signed_z=83.558 onset_bin=42 onset_rel_s=317.655 persistence_bins=3
values_compact=delta:0.010846,-0.004759,-0.000127,0,0.000657,0.000656,-0.002337,0,0.007918,0,-0.003774,-0.003773,-0.000028,-0.000027,0.003081,0.003081,-0.003164,-0.003164,0,0.000389,0,0.002219,0,-0.000011,0,-0.000878,0,0,0.000338,-0.000401,0,-0.000313,0,-0.000226,0,-0.000982,0,0.001382,0,0,-0.002176,0,0.22119,0,-0.109634,-0.109634,-0.001428,0,0.000032,0,0.000981,0,0.000457,0,-0.002155,0,0.000304,0,0.001499,0,-0.001713,0,0.000739,-0.000627
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,1,2
[M3] rank=3 service=ts-cancel-service metric=k8s.pod.cpu_limit_utilization baseline=0.001456 peak=0.045123 signed_z=83.558 onset_bin=42 onset_rel_s=317.655 persistence_bins=3
values_compact=delta:0.002169,-0.000952,-0.000025,0,0.000131,0.000132,-0.000468,0,0.001584,0,-0.000755,-0.000755,-0.000005,-0.000006,0.000617,0.000616,-0.000633,-0.000633,0,0.000078,0,0.000444,0,-0.000002,0,-0.000176,0,0,0.000068,-0.000081,0,-0.000062,0,-0.000045,0,-0.000197,0,0.000277,0,0,-0.000436,0,0.044238,0,-0.021926,-0.021927,-0.000286,0,0.000007,0,0.000196,0,0.000091,0,-0.000431,0,0.000061,0,0.0003,0,-0.000343,0,0.000148,-0.000125
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,1,2
[M4] rank=4 service=ts-cancel-service metric=container.cpu.usage baseline=0.006911 peak=0.171889 signed_z=67.694 onset_bin=41 onset_rel_s=310.181 persistence_bins=3
values_compact=delta:0.00585,0.0002,0,0.000012,0,0.001261,0,0,-0.002359,0.011864,-0.006414,-0.006414,0.000886,0.000886,0.00198,0.001979,-0.004402,0,-0.000015,-0.000014,0.001112,0.001113,0.000102,0.000102,-0.000535,-0.000535,0,-0.000057,0.000796,0.000796,0,-0.001757,0,-0.000318,-0.000426,-0.000425,0.000854,0.000855,-0.001152,-0.001151,0,0.167215,0,0,-0.166167,-0.000132,0,-0.000651,0,0.001356,-0.000616,-0.000615,0.000501,0.000501,-0.000756,-0.000756,-0.000111,-0.000111,0.002413,-0.002534,0,0.001277,0,-0.000768
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,1,2
[M5] rank=5 service=ts-cancel-service metric=container.memory.rss baseline=679953322.666667 peak=687230976.0 signed_z=28.427 onset_bin=41 onset_rel_s=310.181 persistence_bins=23
values_compact=delta:679612416,0,0,4096,0,-98304,0,0,0,471040,0,0,20480,20480,137216,137216,-126976,0,0,0,26624,26624,-75776,-75776,0,0,0,0,4096,4096,0,4096,0,0,0,0,112640,112640,8192,8192,0,6651904,0,0,-61440,12288,0,0,0,4096,0,0,51200,51200,61440,61440,0,0,24576,0,0,40960,0,-67584
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,1,2
[M6] rank=6 service=ts-cancel-service metric=k8s.pod.memory.rss baseline=679991722.666667 peak=687267840.0 signed_z=28.295 onset_bin=42 onset_rel_s=317.655 persistence_bins=22
values_compact=delta:679649280,0,0,0,-47104,-47104,0,0,212992,0,129024,129024,20480,20480,137216,137216,-63488,-63488,0,0,0,65536,0,-163840,0,0,0,0,8192,0,0,4096,0,0,0,0,0,241664,0,0,0,0,6651904,0,-24576,-24576,0,0,0,0,4096,0,102400,0,0,0,122880,0,24576,0,0,0,40960,-67584
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,1,2
[M7] rank=7 service=ts-cancel-service metric=container.memory.available baseline=2530888277.333333 peak=2523668480.0 signed_z=-26.875 onset_bin=41 onset_rel_s=310.181 persistence_bins=23
values_compact=delta:2531213312,0,0,-4096,0,155648,0,0,0,-589824,0,0,-16384,-16384,-141312,-141312,180224,0,0,0,-26624,-26624,118784,118784,0,0,0,0,-4096,-4096,0,-4096,0,0,0,0,-147456,-147456,-8192,-8192,0,-6664192,0,0,131072,-12288,0,0,0,-4096,0,0,-51200,-51200,-59392,-59392,0,0,-24576,0,0,-36864,0,92160
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,1,2
[M8] rank=8 service=ts-cancel-service metric=container.memory.usage baseline=690722218.666667 peak=697942016.0 signed_z=26.875 onset_bin=41 onset_rel_s=310.181 persistence_bins=23
values_compact=delta:690397184,0,0,4096,0,-155648,0,0,0,589824,0,0,16384,16384,141312,141312,-180224,0,0,0,26624,26624,-118784,-118784,0,0,0,0,4096,4096,0,4096,0,0,0,0,147456,147456,8192,8192,0,6664192,0,0,-131072,12288,0,0,0,4096,0,0,51200,51200,59392,59392,0,0,24576,0,0,36864,0,-92160
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,1,2
[M9] rank=9 service=ts-cancel-service metric=container.memory.working_set baseline=690337194.666667 peak=697556992.0 signed_z=26.875 onset_bin=41 onset_rel_s=310.181 persistence_bins=23
values_compact=delta:690012160,0,0,4096,0,-155648,0,0,0,589824,0,0,16384,16384,141312,141312,-180224,0,0,0,26624,26624,-118784,-118784,0,0,0,0,4096,4096,0,4096,0,0,0,0,147456,147456,8192,8192,0,6664192,0,0,-131072,12288,0,0,0,4096,0,0,51200,51200,59392,59392,0,0,24576,0,0,36864,0,-92160
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,1,2
[M10] rank=10 service=ts-cancel-service metric=k8s.pod.memory.available baseline=2530120960.0 peak=2522988544.0 signed_z=-20.984 onset_bin=42 onset_rel_s=317.655 persistence_bins=22
values_compact=delta:2530533376,0,0,0,75776,75776,0,0,-1282048,0,346112,346112,-16384,-16384,-141312,-141312,90112,90112,0,0,0,-65536,0,249856,0,0,0,0,-8192,0,0,-4096,0,0,0,0,0,-311296,0,0,0,0,-6664192,0,59392,59392,0,0,0,0,-4096,0,-102400,0,0,0,-118784,0,-24576,0,0,0,-36864,92160
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,1,2
[M11] rank=11 service=ts-cancel-service metric=k8s.pod.memory.usage baseline=691489536.0 peak=698621952.0 signed_z=20.984 onset_bin=42 onset_rel_s=317.655 persistence_bins=22
values_compact=delta:691077120,0,0,0,-75776,-75776,0,0,1282048,0,-346112,-346112,16384,16384,141312,141312,-90112,-90112,0,0,0,65536,0,-249856,0,0,0,0,8192,0,0,4096,0,0,0,0,0,311296,0,0,0,0,6664192,0,-59392,-59392,0,0,0,0,4096,0,102400,0,0,0,118784,0,24576,0,0,0,36864,-92160
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,1,2
[M12] rank=12 service=ts-cancel-service metric=k8s.pod.memory.working_set baseline=691104512.0 peak=698236928.0 signed_z=20.984 onset_bin=42 onset_rel_s=317.655 persistence_bins=22
values_compact=delta:690692096,0,0,0,-75776,-75776,0,0,1282048,0,-346112,-346112,16384,16384,141312,141312,-90112,-90112,0,0,0,65536,0,-249856,0,0,0,0,8192,0,0,4096,0,0,0,0,0,311296,0,0,0,0,6664192,0,-59392,-59392,0,0,0,0,4096,0,102400,0,0,0,118784,0,24576,0,0,0,36864,-92160
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,1,2

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[310.98441076278687,336.00002884864807]

=== LOG SUMMARY ===
{"entries":[{"error_logs":4121,"error_pct":19.19,"service":"ts-seat-service","total_logs":21478},{"error_logs":398,"error_pct":15.73,"service":"ts-food-service","total_logs":2530},{"error_logs":173,"error_pct":6.03,"service":"ts-preserve-service","total_logs":2869},{"error_logs":173,"error_pct":2.21,"service":"ts-order-service","total_logs":7842},{"error_logs":96,"error_pct":25.0,"service":"ts-notification-service","total_logs":384},{"error_logs":96,"error_pct":25.0,"service":"ts-delivery-service","total_logs":384},{"error_logs":9,"error_pct":0.58,"service":"ts-route-plan-service","total_logs":1542},{"error_logs":9,"error_pct":0.55,"service":"ts-travel-plan-service","total_logs":1624}],"mode":"errors","omitted_services":23,"service_count":31}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":302.5,"error_pct":0.0,"p95_during_ms":3332.9993065999624,"p95_pre_ms":827.9717383000001,"service":"ts-travel-plan-service","spans":2868},{"delta_pct":105.3,"error_pct":0.0,"p95_during_ms":3758.220577,"p95_pre_ms":1830.660371,"service":"ts-route-plan-service","spans":2222},{"delta_pct":-59.0,"error_pct":0.0,"p95_during_ms":177.34378259999997,"p95_pre_ms":432.7079993999969,"service":"ts-preserve-service","spans":1868},{"delta_pct":-45.1,"error_pct":0.0,"p95_during_ms":5.675369999999997,"p95_pre_ms":10.34222725,"service":"ts-assurance-service","spans":874},{"delta_pct":-43.8,"error_pct":0.0,"p95_during_ms":6.561572449999999,"p95_pre_ms":11.672715399999998,"service":"ts-consign-service","spans":1005},{"delta_pct":-22.1,"error_pct":0.0,"p95_during_ms":4.5054796,"p95_pre_ms":5.781039400000001,"service":"ts-train-food-service","spans":3098},{"delta_pct":-21.8,"error_pct":0.0,"p95_during_ms":7.9209366,"p95_pre_ms":10.134146399999995,"service":"ts-station-food-service","spans":2236},{"delta_pct":-20.1,"error_pct":0.0,"p95_during_ms":68.62756759999998,"p95_pre_ms":85.85378439999995,"service":"ts-travel-service","spans":11677}],"omitted_services":22,"service_count":30}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=35 omitted_edges=0
[{"evidence_source":"metric","onset_rel_s":267.0,"rank":1,"service":"ts-preserve-service","severity_z":18.784},{"evidence_source":"metric","onset_rel_s":270.0,"rank":2,"service":"ts-seat-service","severity_z":18.543},{"evidence_source":"metric","onset_rel_s":316.2,"rank":3,"service":"ts-cancel-service","severity_z":83.558},{"evidence_source":"metric","onset_rel_s":346.8,"rank":4,"service":"loadgenerator","severity_z":15.353},{"evidence_source":"metric","onset_rel_s":346.8,"rank":5,"service":"mysql","severity_z":15.353},{"evidence_source":"metric","onset_rel_s":346.8,"rank":6,"service":"rabbitmq","severity_z":15.353},{"evidence_source":"metric","onset_rel_s":346.8,"rank":7,"service":"ts-admin-basic-info-service","severity_z":15.353},{"evidence_source":"metric","onset_rel_s":346.8,"rank":8,"service":"ts-admin-travel-service","severity_z":15.353},{"evidence_source":"metric","onset_rel_s":346.8,"rank":9,"service":"ts-consign-service","severity_z":15.353},{"evidence_source":"metric","onset_rel_s":346.8,"rank":10,"service":"ts-security-service","severity_z":15.353},{"evidence_source":"metric","onset_rel_s":346.8,"rank":11,"service":"ts-station-service","severity_z":15.353},{"evidence_source":"trace","onset_rel_s":373.8,"rank":12,"service":"ts-basic-service","severity_z":6.927},{"evidence_source":"trace","onset_rel_s":373.8,"rank":13,"service":"ts-config-service","severity_z":6.844},{"evidence_source":"metric","onset_rel_s":400.2,"rank":14,"service":"ts-avatar-service","severity_z":15.343}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"ts-station-service","caller":"ts-basic-service"},{"callee":"ts-basic-service","caller":"ts-preserve-service"},{"callee":"ts-seat-service","caller":"ts-preserve-service"},{"callee":"ts-security-service","caller":"ts-preserve-service"},{"callee":"ts-config-service","caller":"ts-seat-service"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

[excluded before optimizer]

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
opaque_id: INC-34A46D756694
observation_window={"duration_rel_s":478.277,"source_metric_rows":1078}
selection_summary={"candidate_count":104,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":1014,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["loadgenerator","loadgenerator-8465b66847-f65qd","mysql","mysql-0","rabbitmq","rabbitmq-0","ts-admin-basic-info-service","ts-admin-basic-info-service-c7f4d66f9-p9qsf","ts-admin-order-service","ts-admin-order-service-8578fdc446-fq745","ts-admin-route-service","ts-admin-route-service-5d945db787-hqgcw","ts-admin-travel-service","ts-admin-travel-service-96cbcb44b-h8r9z","ts-admin-user-service","ts-admin-user-service-5d8d74d79c-5qtn5","ts-assurance-service","ts-assurance-service-79876db68f-cpwsh","ts-auth-service","ts-auth-service-5dd97d5ccd-bclzf","ts-avatar-service","ts-avatar-service-9b66c896d-vnw29","ts-basic-service","ts-basic-service-68f7cbd746-n6s66","ts-cancel-service","ts-cancel-service-6cb859955d-7jczm","ts-config-service","ts-config-service-7c55667486-cnqz7","ts-consign-price-service","ts-consign-price-service-6cffbf7945-j9j48","ts-consign-service","ts-consign-service-745946dd49-dn9tg","ts-contacts-service","ts-contacts-service-657d4cdfbf-7bc4c","ts-delivery-service","ts-delivery-service-6b488868b8-kqft2","ts-execute-service","ts-execute-service-86d5f5db59-j4hbl","ts-food-delivery-service","ts-food-delivery-service-56447bd89f-6kkp9","ts-food-service","ts-food-service-5fd45cf66d-qcml9","ts-gateway-service","ts-gateway-service-669b9cf6bb-4bctb","ts-inside-payment-service","ts-inside-payment-service-5548965b7f-zr2pd","ts-news-service","ts-news-service-6d6c6d7855-f74qm","ts-notification-service","ts-notification-service-5f7c7d45c9-9hwgh","ts-order-other-service","ts-order-other-service-68fb6fd887-xq96s","ts-order-service","ts-order-service-56b9db98d8-b9g54","ts-payment-service","ts-payment-service-7648bd9bcd-rwlff","ts-preserve-other-service","ts-preserve-other-service-5748c886c9-9knkc","ts-preserve-service","ts-preserve-service-7684df89bd-9rbgh","ts-price-service","ts-price-service-7494fb49fc-8shk4","ts-rebook-service","ts-rebook-service-546f7bdbbd-hfcx6","ts-route-plan-service","ts-route-plan-service-d9557d6d7-gptsd","ts-route-service","ts-route-service-86dcd6b94f-25v86","ts-seat-service","ts-seat-service-75676c6d97-7p8ql","ts-security-service","ts-security-service-7cddbd789d-7csgf","ts-station-food-service","ts-station-food-service-8c666b479-5cjl6","ts-station-service","ts-station-service-7ff47b8db8-qvpqm","ts-ticket-office-service","ts-ticket-office-service-5c75d795c-lg6dc","ts-train-food-service","ts-train-food-service-7b67f6b66f-dsd4z","ts-train-service","ts-train-service-7b65db49f4-p2h89","ts-travel-plan-service","ts-travel-plan-service-5b7bdc7c56-nmlmk","ts-travel-service","ts-travel-service-7f856dcb7b-mkdn2","ts-travel2-service","ts-travel2-service-79fb6f545d-6fn6q","ts-ui-dashboard","ts-ui-dashboard-64f6f55bb5-78qmz","ts-user-service","ts-user-service-58c56cb98c-6l52x","ts-verification-code-service","ts-verification-code-service-57cddfb855-d9cr9","ts-voucher-service","ts-voucher-service-6b7fbfc649-b5s9h","ts-wait-order-service","ts-wait-order-service-74df69f44-msc6f","worker1","worker2","worker3","worker4","worker5","worker6"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[3.737,11.21,18.683,26.156,33.629,41.102,48.575,56.048,63.521,70.994,78.467,85.94,93.413,100.887,108.36,115.833,123.306,130.779,138.252,145.725,153.198,160.671,168.144,175.617,183.09,190.563,198.037,205.51,212.983,220.456,227.929,235.402,242.875,250.348,257.821,265.294,272.767,280.24,287.714,295.187,302.66,310.133,317.606,325.079,332.552,340.025,347.498,354.971,362.444,369.917,377.39,384.864,392.337,399.81,407.283,414.756,422.229,429.702,437.175,444.648,452.121,459.594,467.067,474.54]
[M1] rank=1 service=ts-auth-service metric=hubble_http_request_duration_p99_seconds baseline=0.007652 peak=0.2206 signed_z=184.094 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.0107,-0.00332,-0.000288,0.000173,0.000088,-0.000159,-0.000119,0.000083,-0.00027,0,-0.000688,0.000963,-0.002213,0.002175,0.004475,0.209
missing_mask_bits=1101110111011101110111011101110111011101110111011101110111011101
observed_counts_compact=csv:0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0
[M2] rank=2 service=ts-delivery-service metric=container.cpu.usage baseline=0.006705 peak=0.093258 signed_z=69.712 onset_bin=45 onset_rel_s=340.025 persistence_bins=2
values_compact=delta:0.006619,0,-0.000174,0,-0.001001,0,0.002591,0,0.00014,0.00014,-0.001553,0,-0.000399,0,0.000721,0,0.001543,0.001544,-0.002505,-0.002504,0,0.001677,0,-0.001052,-0.000092,-0.000092,0,-0.000182,0.000556,0.000556,0,0.00066,-0.000987,-0.000987,0,0.0015,0,-0.001373,0,0.003671,0,-0.003304,-0.000442,-0.000443,0,0.08843,0,-0.085484,0,-0.0018,0,-0.000165,-0.000166,0.000198,0.000197,0.000579,-0.001271,0,0,0.000301,0,-0.000068,-0.000068,0.000232
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M3] rank=3 service=ts-delivery-service metric=k8s.pod.cpu_limit_utilization baseline=0.00135 peak=0.015932 signed_z=61.145 onset_bin=43 onset_rel_s=325.079 persistence_bins=3
values_compact=delta:0.001307,0.00006,-0.000064,-0.000065,-0.000066,-0.000067,0.000177,0.000176,0.000127,0.000128,-0.000157,-0.000156,-0.000038,-0.000039,0.000101,0,0.000483,0,-0.000259,-0.00026,0.000019,0.000018,-0.000318,0,-0.000048,0,0.000049,0.000049,0,0.000002,0,0.000305,0,-0.000251,0,0.00004,0,0,-0.000149,0.000735,0,-0.00049,0,0.014583,0,-0.00738,-0.007381,0.000256,0,-0.000173,0,-0.000064,-0.000064,0.000028,0.000027,0,0.000039,-0.000052,-0.000053,0.000001,0,0,0.000034,-0.000014
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M4] rank=4 service=ts-delivery-service metric=k8s.pod.cpu.node.utilization baseline=5.3e-05 peak=0.000622 signed_z=61.145 onset_bin=43 onset_rel_s=325.079 persistence_bins=3
values_compact=delta:0.000051,0.000002,-0.000002,-0.000003,-0.000002,-0.000003,0.000007,0.000007,0.000005,0.000005,-0.000006,-0.000006,-0.000002,-0.000001,0.000004,0,0.000019,0,-0.000011,-0.00001,0.000001,0.000001,-0.000013,0,-0.000002,0,0.000002,0.000002,0,0,0,0.000012,0,-0.00001,0,0.000002,0,0,-0.000006,0.000029,0,-0.000019,0,0.000569,0,-0.000288,-0.000288,0.00001,0,-0.000007,0,-0.000003,-0.000002,0.000001,0.000001,0,0.000002,-0.000002,-0.000002,0,0,0,0.000001,-0.000001
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M5] rank=5 service=ts-delivery-service metric=k8s.pod.cpu.usage baseline=0.006748 peak=0.07966 signed_z=61.145 onset_bin=43 onset_rel_s=325.079 persistence_bins=3
values_compact=delta:0.006533,0.000304,-0.000323,-0.000323,-0.000333,-0.000332,0.000882,0.000882,0.000636,0.000637,-0.000783,-0.000782,-0.00019,-0.000191,0.000504,0,0.002416,0,-0.001298,-0.001298,0.000092,0.000092,-0.00159,0,-0.000242,0,0.000246,0.000246,0,0.000011,0,0.001522,0,-0.001254,0,0.000199,0,0,-0.000744,0.003677,0,-0.002451,0,0.072915,0,-0.036902,-0.036903,0.001278,0,-0.000862,0,-0.00032,-0.000319,0.000137,0.000137,0,0.000195,-0.000263,-0.000263,0.000004,0.000003,0,0.000167,-0.000068
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M6] rank=6 service=ts-cancel-service metric=container.memory.available baseline=2555984213.333333 peak=2548465664.0 signed_z=-52.381 onset_bin=33 onset_rel_s=250.348 persistence_bins=31
values_compact=delta:2556137472,106496,0,0,0,0,-557056,90112,90112,0,4096,0,0,40960,94208,-4096,-4096,0,0,0,0,0,0,0,-24576,0,0,0,0,0,0,-282624,0,-790528,102400,0,0,0,0,-6537216,204800,0,0,0,0,-4096,-4096,0,-40960,0,0,0,0,0,-4096,-6144,-6144,0,0,0,0,0,0,-10240
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M7] rank=7 service=ts-cancel-service metric=container.memory.usage baseline=665626282.666667 peak=673144832.0 signed_z=52.381 onset_bin=33 onset_rel_s=250.348 persistence_bins=31
values_compact=delta:665473024,-106496,0,0,0,0,557056,-90112,-90112,0,-4096,0,0,-40960,-94208,4096,4096,0,0,0,0,0,0,0,24576,0,0,0,0,0,0,282624,0,790528,-102400,0,0,0,0,6537216,-204800,0,0,0,0,4096,4096,0,40960,0,0,0,0,0,4096,6144,6144,0,0,0,0,0,0,10240
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M8] rank=8 service=ts-cancel-service metric=container.memory.working_set baseline=665241258.666667 peak=672759808.0 signed_z=52.381 onset_bin=33 onset_rel_s=250.348 persistence_bins=31
values_compact=delta:665088000,-106496,0,0,0,0,557056,-90112,-90112,0,-4096,0,0,-40960,-94208,4096,4096,0,0,0,0,0,0,0,24576,0,0,0,0,0,0,282624,0,790528,-102400,0,0,0,0,6537216,-204800,0,0,0,0,4096,4096,0,40960,0,0,0,0,0,4096,6144,6144,0,0,0,0,0,0,10240
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M9] rank=9 service=ts-cancel-service metric=container.memory.rss baseline=654904746.666667 peak=662396928.0 signed_z=46.439 onset_bin=33 onset_rel_s=250.348 persistence_bins=31
values_compact=delta:654643200,-61440,0,0,0,0,557056,-65536,-65536,0,0,0,0,-16384,-69632,4096,4096,0,0,0,0,0,0,0,16384,0,0,0,0,0,0,229376,0,712704,-65536,0,0,0,0,6574080,-151552,0,0,0,0,4096,4096,0,40960,0,0,0,0,0,4096,6144,6144,0,0,0,0,0,0,10240
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M10] rank=10 service=ts-cancel-service metric=k8s.pod.memory.rss baseline=654972330.666667 peak=662376448.0 signed_z=45.089 onset_bin=33 onset_rel_s=250.348 persistence_bins=31
values_compact=delta:654622720,0,2048,2048,301056,301056,0,-88064,-88064,0,0,8192,0,-94208,0,8192,0,0,0,0,0,0,0,16384,0,0,0,0,0,0,0,229376,0,712704,-65536,0,0,0,0,3211264,3211264,0,0,0,4096,0,45056,0,0,0,0,0,0,4096,12288,0,0,0,0,0,0,0,0,10240
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M11] rank=11 service=ts-cancel-service metric=k8s.pod.cpu.node.utilization baseline=5.3e-05 peak=0.00137 signed_z=44.054 onset_bin=39 onset_rel_s=295.187 persistence_bins=3
values_compact=delta:0.000127,0,-0.000044,-0.000045,0.000036,0.000037,0,-0.000033,-0.000033,-0.000005,0,-0.000003,0,0.000004,0,0.000002,0,-0.000005,0,0,0.000001,-0.000003,0,0.000011,0,-0.000005,-0.000005,0.000001,0.000001,-0.000002,-0.000001,0.000014,0,0.000124,-0.000137,0,0.000001,0,-0.000002,0.000667,0.000667,0,-0.001335,0,0.000004,0,0.00001,0,0,-0.000013,0,0,0,0.000002,0.000012,0,-0.000015,0.000001,0.000002,0,-0.000003,0,0,0.000001
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M12] rank=12 service=ts-cancel-service metric=k8s.pod.cpu.usage baseline=0.006836 peak=0.175313 signed_z=44.054 onset_bin=39 onset_rel_s=295.187 persistence_bins=3
values_compact=delta:0.016314,0,-0.005742,-0.005743,0.004695,0.004695,0,-0.004205,-0.004205,-0.000748,0,-0.000314,0,0.000555,0,0.00023,0,-0.000719,0,0.000066,0.000066,-0.000382,0,0.001466,0,-0.000654,-0.000655,0.000115,0.000116,-0.000153,-0.000153,0.001722,0,0.015944,-0.017605,0,0.000123,0,-0.00024,0.085362,0.085362,0,-0.170817,0,0.000543,0,0.001201,0,0,-0.001668,0,0.000052,0,0.000238,0.001538,0,-0.001917,0.000188,0.000187,0,-0.000433,0.000052,0.000052,0.000121
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[437.7519109249115,467.7519109249115]

=== LOG SUMMARY ===
{"entries":[{"error_logs":14521,"error_pct":100.0,"service":"ts-ui-dashboard","total_logs":14521},{"error_logs":629,"error_pct":16.34,"service":"ts-food-service","total_logs":3849},{"error_logs":253,"error_pct":6.39,"service":"ts-preserve-service","total_logs":3959},{"error_logs":253,"error_pct":2.16,"service":"ts-order-service","total_logs":11691},{"error_logs":96,"error_pct":25.0,"service":"ts-delivery-service","total_logs":384},{"error_logs":96,"error_pct":25.0,"service":"ts-notification-service","total_logs":384},{"error_logs":4,"error_pct":3.64,"service":"ts-inside-payment-service","total_logs":110},{"error_logs":2,"error_pct":3.7,"service":"ts-payment-service","total_logs":54}],"mode":"errors","omitted_services":23,"service_count":31}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":-48.3,"error_pct":0.0,"p95_during_ms":6.150395400000001,"p95_pre_ms":11.906315849999991,"service":"ts-consign-service","spans":1228},{"delta_pct":-33.5,"error_pct":0.0,"p95_during_ms":9.037847999999997,"p95_pre_ms":13.594992799999998,"service":"ts-payment-service","spans":510},{"delta_pct":-28.4,"error_pct":0.0,"p95_during_ms":6.342216249999993,"p95_pre_ms":8.854091,"service":"ts-assurance-service","spans":1120},{"delta_pct":-25.2,"error_pct":0.0,"p95_during_ms":335.40756539999995,"p95_pre_ms":448.11901274999985,"service":"ts-route-plan-service","spans":3351},{"delta_pct":-25.2,"error_pct":0.0,"p95_during_ms":450.15391399999993,"p95_pre_ms":601.7428048,"service":"ts-travel-plan-service","spans":4479},{"delta_pct":18.9,"error_pct":0.0,"p95_during_ms":388.9934825999991,"p95_pre_ms":327.0284989999999,"service":"ts-preserve-service","spans":2589},{"delta_pct":-17.6,"error_pct":0.0,"p95_during_ms":2.57063565,"p95_pre_ms":3.11825865,"service":"ts-config-service","spans":31200},{"delta_pct":-17.3,"error_pct":0.0,"p95_during_ms":2.6746201999999997,"p95_pre_ms":3.2335724,"service":"ts-verification-code-service","spans":9200}],"omitted_services":22,"service_count":30}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=35 omitted_edges=0
[{"evidence_source":"metric","onset_rel_s":240.6,"rank":1,"service":"ts-gateway-service","severity_z":12.519},{"evidence_source":"metric","onset_rel_s":261.0,"rank":2,"service":"ts-config-service","severity_z":11.195},{"evidence_source":"metric","onset_rel_s":276.0,"rank":3,"service":"ts-contacts-service","severity_z":10.077},{"evidence_source":"metric","onset_rel_s":292.2,"rank":4,"service":"ts-cancel-service","severity_z":52.381},{"evidence_source":"metric","onset_rel_s":294.0,"rank":5,"service":"ts-security-service","severity_z":10.537},{"evidence_source":"metric","onset_rel_s":297.0,"rank":6,"service":"ts-order-service","severity_z":16.864},{"evidence_source":"metric","onset_rel_s":334.8,"rank":7,"service":"ts-notification-service","severity_z":10.201},{"evidence_source":"metric","onset_rel_s":336.6,"rank":8,"service":"ts-delivery-service","severity_z":69.712},{"evidence_source":"metric","onset_rel_s":348.6,"rank":9,"service":"ts-consign-service","severity_z":21.188},{"evidence_source":"metric","onset_rel_s":349.2,"rank":10,"service":"ts-admin-travel-service","severity_z":12.683},{"evidence_source":"metric","onset_rel_s":369.6,"rank":11,"service":"ts-train-food-service","severity_z":28.659},{"evidence_source":"metric","onset_rel_s":467.4,"rank":12,"service":"ts-route-plan-service","severity_z":18.52},{"evidence_source":"metric","onset_rel_s":468.0,"rank":13,"service":"ts-auth-service","severity_z":184.094},{"evidence_source":"none","onset_rel_s":null,"rank":14,"service":"ts-preserve-service","severity_z":0.0}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"ts-order-service","caller":"ts-cancel-service"},{"callee":"ts-contacts-service","caller":"ts-preserve-service"},{"callee":"ts-order-service","caller":"ts-preserve-service"},{"callee":"ts-security-service","caller":"ts-preserve-service"},{"callee":"ts-order-service","caller":"ts-security-service"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

[excluded before optimizer]

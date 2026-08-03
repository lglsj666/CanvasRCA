# Allocation conversation — INC-0F75AF2139D7 — full_text_only

Private evaluator case id: `aegislab_ts4-ts-consign-service-latency-g5fj65`

## System

You are an expert Site Reliability Engineer performing Root Cause Analysis (RCA) for a microservice application deployed on a Kubernetes cluster. A fault has occurred in the system. Your task is to identify the root cause of the incident.

Root causes can occur at three levels:
- Pod level: a specific container replica (e.g., "cartservice-0")
- Service level: a microservice type (e.g., "paymentservice") — predict any pod of that service
- Node level: an infrastructure host (e.g., "node-6") — nodes appear as isolated entities with system metrics (CPU, memory, network, disk) but no application logs or traces

The system consists of multiple services communicating over HTTP/gRPC, running on shared infrastructure nodes. A fault in one component (pod, service, or node) can propagate to dependent components, causing them to appear degraded even though they are not the root cause.

Node-level faults (e.g., host memory exhaustion, CPU saturation, disk I/O) often manifest as correlated anomalies across multiple pods. If several unrelated pods show simultaneous degradation and a node shows critical system-level metrics, the node is likely the root cause.

Focus on distinguishing the ORIGIN of the fault from its SYMPTOMS in downstream or co-located components.

## User

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
opaque_id: INC-0F75AF2139D7
observation_window={"duration_rel_s":478.915,"source_metric_rows":951}
selection_summary={"candidate_count":104,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":902,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["loadgenerator","loadgenerator-d75cc479f-2zlnw","mysql","mysql-0","rabbitmq","rabbitmq-0","ts-admin-basic-info-service","ts-admin-basic-info-service-66cdcc94bc-lnlvj","ts-admin-order-service","ts-admin-order-service-5b6dc77d7d-2qttf","ts-admin-route-service","ts-admin-route-service-f9c84f85f-lnj8t","ts-admin-travel-service","ts-admin-travel-service-659b5c9df4-64sf8","ts-admin-user-service","ts-admin-user-service-5bfc8844b9-fqtcc","ts-assurance-service","ts-assurance-service-75c854dc5c-6dvhb","ts-auth-service","ts-auth-service-69bdd5df8-9dvk4","ts-avatar-service","ts-avatar-service-845b64df6-nxhg6","ts-basic-service","ts-basic-service-7c6d59d5c4-8mfpx","ts-cancel-service","ts-cancel-service-7ffd988fdb-qq5hp","ts-config-service","ts-config-service-55cffbf48b-ztxl6","ts-consign-price-service","ts-consign-price-service-654cb4fc65-z5nxp","ts-consign-service","ts-consign-service-9954fddf-6rlv2","ts-contacts-service","ts-contacts-service-6d745b6c8f-gg2hw","ts-delivery-service","ts-delivery-service-694895c6cb-svrtj","ts-execute-service","ts-execute-service-8457c56cb7-zbjwc","ts-food-delivery-service","ts-food-delivery-service-96d856899-llqjn","ts-food-service","ts-food-service-64d454885b-j5md5","ts-gateway-service","ts-gateway-service-7f988fb8c4-9vzz7","ts-inside-payment-service","ts-inside-payment-service-5ccb8ccb87-swxz9","ts-news-service","ts-news-service-6d6c6d7855-lhg5d","ts-notification-service","ts-notification-service-58f6c468d7-29tlz","ts-order-other-service","ts-order-other-service-5d6878687f-2vjnc","ts-order-service","ts-order-service-6794d6f564-p49cd","ts-payment-service","ts-payment-service-58854d694-pl8cr","ts-preserve-other-service","ts-preserve-other-service-64fd9c88cf-rgvkp","ts-preserve-service","ts-preserve-service-696df489d4-9jhs5","ts-price-service","ts-price-service-67c895b45-s6k75","ts-rebook-service","ts-rebook-service-7c7644bbdd-zmkdx","ts-route-plan-service","ts-route-plan-service-556cddc5c9-kh55p","ts-route-service","ts-route-service-cfc6dbcf7-nd5dr","ts-seat-service","ts-seat-service-6c78b7d797-6ftxc","ts-security-service","ts-security-service-55f5b777bb-lhhl5","ts-station-food-service","ts-station-food-service-746f6779d7-hw2mz","ts-station-service","ts-station-service-65986cc944-xp2x6","ts-ticket-office-service","ts-ticket-office-service-d7c58b8c7-nvhhm","ts-train-food-service","ts-train-food-service-d5485c677-8ds4t","ts-train-service","ts-train-service-9b56d75b6-g8k55","ts-travel-plan-service","ts-travel-plan-service-7875c49896-gt4zg","ts-travel-service","ts-travel-service-c7b5c6d9b-rcjf7","ts-travel2-service","ts-travel2-service-7ff5bbbf54-ts8vr","ts-ui-dashboard","ts-ui-dashboard-57867cb85c-4wfjl","ts-user-service","ts-user-service-54dd6b48c-7xrm5","ts-verification-code-service","ts-verification-code-service-85785c4f79-csmjr","ts-voucher-service","ts-voucher-service-689c4fc885-qpn58","ts-wait-order-service","ts-wait-order-service-7cf6bc9468-kdxvn","worker1","worker2","worker3","worker4","worker5","worker6"]

=== METRIC SUMMARY (dense sequences use allocated transport) ===
[M1] rank=1 service=ts-consign-service metric=container.filesystem.usage baseline=466944.0 peak=3080192.0 signed_z=848.404 onset_bin=33 onset_rel_s=250.682 persistence_bins=31
[M2] rank=2 service=ts-cancel-service metric=k8s.pod.cpu_limit_utilization baseline=0.001986 peak=0.09168 signed_z=85.653 onset_bin=None onset_rel_s=None persistence_bins=0
[M3] rank=3 service=ts-cancel-service metric=k8s.pod.cpu.node.utilization baseline=7.8e-05 peak=0.003581 signed_z=85.653 onset_bin=None onset_rel_s=None persistence_bins=0
[M4] rank=4 service=ts-cancel-service metric=k8s.pod.cpu.usage baseline=0.009931 peak=0.458401 signed_z=85.653 onset_bin=None onset_rel_s=None persistence_bins=0
[M5] rank=5 service=ts-cancel-service metric=container.cpu.usage baseline=0.009091 peak=0.351551 signed_z=64.351 onset_bin=33 onset_rel_s=250.682 persistence_bins=2
[M6] rank=6 service=ts-consign-service metric=k8s.pod.filesystem.usage baseline=1654261.106383 peak=4845568.0 signed_z=36.897 onset_bin=33 onset_rel_s=250.682 persistence_bins=31
[M7] rank=7 service=ts-news-service metric=k8s.pod.memory_limit_utilization baseline=0.003611 peak=0.003633 signed_z=34.987 onset_bin=49 onset_rel_s=370.41 persistence_bins=15
[M8] rank=8 service=ts-news-service metric=k8s.pod.memory.node.utilization baseline=8.6e-05 peak=8.7e-05 signed_z=34.987 onset_bin=0 onset_rel_s=3.742 persistence_bins=64
[M9] rank=9 service=ts-news-service metric=container.memory.usage baseline=10942507.574468 peak=11014144.0 signed_z=34.987 onset_bin=48 onset_rel_s=362.927 persistence_bins=16
[M10] rank=10 service=ts-news-service metric=container.memory.working_set baseline=10942507.574468 peak=11014144.0 signed_z=34.987 onset_bin=48 onset_rel_s=362.927 persistence_bins=16
[M11] rank=11 service=ts-news-service metric=k8s.pod.memory.usage baseline=11630635.574468 peak=11702272.0 signed_z=34.987 onset_bin=49 onset_rel_s=370.41 persistence_bins=15
[M12] rank=12 service=ts-news-service metric=k8s.pod.memory.working_set baseline=11630635.574468 peak=11702272.0 signed_z=34.987 onset_bin=49 onset_rel_s=370.41 persistence_bins=15

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[244.34192657470703,474.2918109893799]

=== LOG SUMMARY ===
{"entries":[{"error_logs":4700,"error_pct":19.2,"service":"ts-seat-service","total_logs":24478},{"error_logs":474,"error_pct":16.3,"service":"ts-food-service","total_logs":2908},{"error_logs":187,"error_pct":6.12,"service":"ts-preserve-service","total_logs":3055},{"error_logs":187,"error_pct":2.13,"service":"ts-order-service","total_logs":8784},{"error_logs":96,"error_pct":25.0,"service":"ts-delivery-service","total_logs":384},{"error_logs":95,"error_pct":25.0,"service":"ts-notification-service","total_logs":380},{"error_logs":2,"error_pct":0.27,"service":"ts-consign-service","total_logs":731},{"error_logs":2,"error_pct":0.02,"service":"ts-ui-dashboard","total_logs":10796}],"mode":"errors","omitted_services":23,"service_count":31}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":-64.3,"error_pct":1.47,"p95_during_ms":13.999015099999989,"p95_pre_ms":39.1842835,"service":"ts-consign-service","spans":853},{"delta_pct":-61.8,"error_pct":0.0,"p95_during_ms":53.9756672,"p95_pre_ms":141.13031659999993,"service":"ts-cancel-service","spans":36},{"delta_pct":-57.4,"error_pct":0.0,"p95_during_ms":4.800885149999999,"p95_pre_ms":11.271047399999977,"service":"ts-order-service","spans":23161},{"delta_pct":-56.4,"error_pct":0.0,"p95_during_ms":4.29191385,"p95_pre_ms":9.839393,"service":"ts-train-service","spans":15225},{"delta_pct":-56.2,"error_pct":0.0,"p95_during_ms":38.41511065000002,"p95_pre_ms":87.67611384999991,"service":"ts-basic-service","spans":10368},{"delta_pct":-51.1,"error_pct":0.0,"p95_during_ms":16.0419445,"p95_pre_ms":32.795477299999924,"service":"ts-seat-service","spans":19536},{"delta_pct":-49.8,"error_pct":0.0,"p95_during_ms":4.7578,"p95_pre_ms":9.482356600000008,"service":"ts-order-other-service","spans":14170},{"delta_pct":-48.9,"error_pct":0.0,"p95_during_ms":5.2847536999999996,"p95_pre_ms":10.3477862,"service":"ts-train-food-service","spans":3574}],"omitted_services":22,"service_count":30}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=35 omitted_edges=1
[{"evidence_source":"metric","onset_rel_s":249.0,"rank":1,"service":"ts-cancel-service","severity_z":85.653},{"evidence_source":"metric","onset_rel_s":249.6,"rank":2,"service":"ts-travel-plan-service","severity_z":18.822},{"evidence_source":"metric","onset_rel_s":252.6,"rank":3,"service":"mysql","severity_z":13.147},{"evidence_source":"trace","onset_rel_s":304.2,"rank":4,"service":"ts-consign-service","severity_z":122.345},{"evidence_source":"metric","onset_rel_s":310.8,"rank":5,"service":"ts-train-food-service","severity_z":30.449},{"evidence_source":"metric","onset_rel_s":322.2,"rank":6,"service":"rabbitmq","severity_z":11.694},{"evidence_source":"metric","onset_rel_s":337.2,"rank":7,"service":"ts-config-service","severity_z":13.376},{"evidence_source":"metric","onset_rel_s":355.2,"rank":8,"service":"ts-travel2-service","severity_z":12.464},{"evidence_source":"metric","onset_rel_s":356.4,"rank":9,"service":"ts-order-service","severity_z":25.062},{"evidence_source":"metric","onset_rel_s":356.4,"rank":10,"service":"ts-seat-service","severity_z":11.562},{"evidence_source":"metric","onset_rel_s":369.0,"rank":11,"service":"ts-news-service","severity_z":34.987},{"evidence_source":"metric","onset_rel_s":370.8,"rank":12,"service":"ts-preserve-service","severity_z":14.768},{"evidence_source":"metric","onset_rel_s":382.2,"rank":13,"service":"ts-security-service","severity_z":28.821},{"evidence_source":"metric","onset_rel_s":384.0,"rank":14,"service":"ts-auth-service","severity_z":11.617}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

=== DENSE METRIC TRANSPORT (lossless) ===
shared_bin_centers_rel_s=[3.742,11.225,18.708,26.191,33.674,41.157,48.64,56.123,63.606,71.089,78.572,86.055,93.538,101.021,108.504,115.987,123.47,130.953,138.436,145.919,153.402,160.885,168.368,175.851,183.334,190.818,198.301,205.784,213.267,220.75,228.233,235.716,243.199,250.682,258.165,265.648,273.131,280.614,288.097,295.58,303.063,310.546,318.029,325.512,332.995,340.478,347.961,355.444,362.927,370.41,377.894,385.377,392.86,400.343,407.826,415.309,422.792,430.275,437.758,445.241,452.724,460.207,467.69,475.173]
[M1]
values_compact=rle:466944*33,3080192*31
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1
[M2]
values_compact=delta:0.001155,0.000006,0.000007,0,0.000417,0,0.000072,0,0.000079,0.0002,0.0002,-0.000154,0,0.000055,0.000056,0.001283,0.001284,0,-0.002932,0,0,-0.000496,-0.000293,0.001185,0.001184,0,-0.000239,-0.001048,-0.001048,0.000096,0,0.000063,0,0.090548,-0.09041,0,0,0.000151,-0.000074,0,0,-0.000071,0,0.00008,0,-0.000128,-0.000128,-0.000098,0,-0.000013,-0.000013,0.000148,0.000148,0.001939,0,-0.001099,-0.0011,0.000105,0,0.00007,0,-0.000129,0,-0.000022
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M3]
values_compact=delta:0.000045,0,0.000001,0,0.000016,0,0.000003,0,0.000003,0.000008,0.000007,-0.000006,0,0.000003,0.000002,0.00005,0.00005,0,-0.000114,0,0,-0.00002,-0.000011,0.000046,0.000046,0,-0.000009,-0.000041,-0.000041,0.000004,0,0.000002,0,0.003537,-0.003531,0,0,0.000005,-0.000002,0,0,-0.000003,0,0.000003,0,-0.000005,-0.000005,-0.000004,0,0,-0.000001,0.000006,0.000006,0.000075,0,-0.000043,-0.000042,0.000004,0,0.000002,0,-0.000005,0,-0.000001
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M4]
values_compact=delta:0.005775,0.000032,0.000032,0,0.002084,0,0.000362,0,0.000396,0.000998,0.000999,-0.000767,0,0.000276,0.000276,0.006419,0.006418,0,-0.014659,0,0,-0.002479,-0.001467,0.005923,0.005923,0,-0.001196,-0.00524,-0.00524,0.000482,0,0.000315,0,0.452739,-0.452052,0,0,0.000755,-0.000368,0,0,-0.000356,0,0.000401,0,-0.000641,-0.000642,-0.000488,0,-0.000064,-0.000064,0.00074,0.00074,0.009694,0,-0.005498,-0.005497,0.000522,0,0.000354,0,-0.000646,0,-0.00011
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M5]
values_compact=delta:0.006009,0,0.000946,0,0.000334,0.000319,0.00032,0.000448,0.000448,0.000103,0.000104,0.000957,0.000957,-0.000162,-0.000163,0.00749,0.007489,-0.008789,-0.008789,0.00041,0,-0.002676,-0.00099,0,0,0.015761,-0.01389,0,-0.001597,0,0,0.000473,0,0.346039,0,-0.344493,0,-0.0001,-0.000101,-0.000452,0,-0.000014,0,0.000107,0.000107,-0.000606,-0.000606,-0.000229,-0.000229,0,0.001084,0.005832,0.005832,0,-0.011637,0,-0.000572,0,0,0.000417,-0.000639,0,-0.000223,0.000073
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M6]
values_compact=delta:1519616,40960,8192,0,0,6144,2048,2048,2048,2048,2048,8192,4096,4096,0,30720,14336,6144,6144,2048,6144,22528,18432,8192,12288,22528,22528,2048,14336,30720,6144,8192,16384,2625536,8192,0,10240,6144,0,0,2048,6144,8192,8192,8192,0,12288,16384,36864,28672,8192,8192,8192,16384,57344,16384,2048,10240,10240,6144,22528,18432,24576,8192
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1
[M7]
values_compact=rle:0.00361*15,0.003611*17,0.00361*17,0.003633*15
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1
[M8]
values_compact=rle:0.000086*49,0.000087*15
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1
[M9]
values_compact=rle:10940416*15,10942464*1,10944512*16,10940416*16,10977280*1,11014144*15
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1
[M10]
values_compact=rle:10940416*15,10942464*1,10944512*16,10940416*16,10977280*1,11014144*15
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1
[M11]
values_compact=rle:11628544*15,11630592*1,11632640*15,11630592*1,11628544*17,11702272*15
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1
[M12]
values_compact=rle:11628544*15,11630592*1,11632640*15,11630592*1,11628544*17,11702272*15
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1
=== DENSE DIRECTED-EDGE TRANSPORT (caller -> callee) ===
[{"callee":"ts-order-service","caller":"ts-cancel-service"},{"callee":"ts-order-service","caller":"ts-preserve-service"},{"callee":"ts-seat-service","caller":"ts-preserve-service"},{"callee":"ts-security-service","caller":"ts-preserve-service"},{"callee":"ts-config-service","caller":"ts-seat-service"},{"callee":"ts-order-service","caller":"ts-seat-service"},{"callee":"ts-order-service","caller":"ts-security-service"},{"callee":"ts-seat-service","caller":"ts-travel-plan-service"},{"callee":"ts-seat-service","caller":"ts-travel2-service"}]

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

## Assistant

{
"services": [
"ts-cancel-service",
"ts-consign-service",
"ts-travel-plan-service"
],
"reason": "ts-cancel-service exhibits the earliest and highest severity metric anomalies (CPU spike at t=249s) preceding downstream trace errors in ts-consign-service and ts-travel-plan-service, indicating it is the origin of the fault rather than a victim of propagation.",
"confidence": "high"
}

## Result

```json
{
  "predicted": [
    "ts-cancel-service",
    "ts-consign-service",
    "ts-travel-plan-service"
  ],
  "rank": 2,
  "mrr": 0.5,
  "top1": false,
  "top3": true,
  "top5": true,
  "ac1": 0.0,
  "ac3": 1.0,
  "ac5": 1.0,
  "avg3": 0.6666666666666666,
  "avg5": 0.8,
  "accepted": [
    "ts-consign-service"
  ]
}
```

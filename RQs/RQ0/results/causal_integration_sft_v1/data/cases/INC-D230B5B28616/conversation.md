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
opaque_id: INC-D230B5B28616
observation_window={"duration_rel_s":479.244,"source_metric_rows":952}
selection_summary={"candidate_count":104,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":914,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["loadgenerator","loadgenerator-5867cb5967-gxvzz","mysql","mysql-0","rabbitmq","rabbitmq-0","ts-admin-basic-info-service","ts-admin-basic-info-service-6659d9d49-5dkcc","ts-admin-order-service","ts-admin-order-service-74874bb64-mdgsd","ts-admin-route-service","ts-admin-route-service-bfb45ff69-tv65k","ts-admin-travel-service","ts-admin-travel-service-685895dffb-dfssw","ts-admin-user-service","ts-admin-user-service-7c45675555-6jhwl","ts-assurance-service","ts-assurance-service-76459f5575-559v5","ts-auth-service","ts-auth-service-5c98dd7948-mxnfv","ts-avatar-service","ts-avatar-service-868fb4bf7d-wktls","ts-basic-service","ts-basic-service-5cdf66d69b-js6hr","ts-cancel-service","ts-cancel-service-55ccd7978d-qf8ml","ts-config-service","ts-config-service-b9bcfbc56-gznnz","ts-consign-price-service","ts-consign-price-service-6749d49475-kdc7k","ts-consign-service","ts-consign-service-b74f9b59f-rvvnc","ts-contacts-service","ts-contacts-service-848bdcc799-mklx5","ts-delivery-service","ts-delivery-service-6f79457966-66vmn","ts-execute-service","ts-execute-service-5dbbc755fc-2g5cs","ts-food-delivery-service","ts-food-delivery-service-74ffc6dbb9-smxk4","ts-food-service","ts-food-service-66b764476b-mfd7n","ts-gateway-service","ts-gateway-service-785597f976-sdg8b","ts-inside-payment-service","ts-inside-payment-service-655f955977-bpvfq","ts-news-service","ts-news-service-7869d45c45-6qqr4","ts-notification-service","ts-notification-service-55b4f48c8f-spbkv","ts-order-other-service","ts-order-other-service-677c8677b5-5ntrl","ts-order-service","ts-order-service-5db685fb54-l2ggq","ts-payment-service","ts-payment-service-58fff7fd68-2qwdz","ts-preserve-other-service","ts-preserve-other-service-745ffd9f57-w7vww","ts-preserve-service","ts-preserve-service-79b467b6c8-45x8z","ts-price-service","ts-price-service-fcbdb55f5-68x7m","ts-rebook-service","ts-rebook-service-67f4f4986-b8lg7","ts-route-plan-service","ts-route-plan-service-6b4859cf65-5qmtc","ts-route-service","ts-route-service-757558799f-j8h9v","ts-seat-service","ts-seat-service-8959d487f-x2v5d","ts-security-service","ts-security-service-5fbb5c757b-m2jtz","ts-station-food-service","ts-station-food-service-864c57dbc7-v4k25","ts-station-service","ts-station-service-774c9cb8b-x29k4","ts-ticket-office-service","ts-ticket-office-service-8687d77bc5-t6kh2","ts-train-food-service","ts-train-food-service-64c578fd99-p4ch9","ts-train-service","ts-train-service-7575645468-vp2r9","ts-travel-plan-service","ts-travel-plan-service-6c75975898-pkxmq","ts-travel-service","ts-travel-service-765c9c9858-sbt4c","ts-travel2-service","ts-travel2-service-5b97989896-z67gm","ts-ui-dashboard","ts-ui-dashboard-69f886fc55-lzjzc","ts-user-service","ts-user-service-d5b9d4bb9-lp4m6","ts-verification-code-service","ts-verification-code-service-57566595bf-4xsjn","ts-voucher-service","ts-voucher-service-69d7fdccff-8lzw9","ts-wait-order-service","ts-wait-order-service-7c88777746-4ww6z","worker1","worker2","worker3","worker4","worker5","worker6"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[3.744,11.232,18.72,26.209,33.697,41.185,48.673,56.161,63.65,71.138,78.626,86.114,93.602,101.09,108.579,116.067,123.555,131.043,138.531,146.02,153.508,160.996,168.484,175.972,183.46,190.949,198.437,205.925,213.413,220.901,228.39,235.878,243.366,250.854,258.342,265.831,273.319,280.807,288.295,295.783,303.271,310.76,318.248,325.736,333.224,340.712,348.201,355.689,363.177,370.665,378.153,385.641,393.13,400.618,408.106,415.594,423.082,430.571,438.059,445.547,453.035,460.523,468.011,475.5]
[M1] rank=1 service=ts-admin-order-service metric=container.cpu.usage baseline=0.005369 peak=0.129418 signed_z=120.899 onset_bin=37 onset_rel_s=280.807 persistence_bins=2
values_compact=delta:0.004254,-0.000166,0.000221,0,0.00033,0.000329,-0.000722,0,-0.000002,0,0.00024,0,0.000332,0.001798,-0.000924,-0.000924,0.00041,0.00041,0,-0.000007,0.000878,0.000877,-0.000526,-0.000526,0.000438,0.000438,-0.000855,-0.000855,0.000116,0,0.000662,0,-0.000845,-0.000846,-0.000235,-0.000236,0,0.125354,0,-0.125187,0,0.000203,-0.000062,-0.000061,0.001672,0,-0.000677,0.000218,0,0,0.000196,0,0.0001,0.000099,-0.000102,0,0.000164,0.000165,-0.000523,-0.000523,0.000386,0.000386,-0.001543,-0.000028
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,2,1,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1
[M2] rank=2 service=ts-admin-order-service metric=container.memory.available baseline=2527840085.333333 peak=2520186880.0 signed_z=-90.049 onset_bin=37 onset_rel_s=280.807 persistence_bins=27
values_compact=delta:2527821824,0,-114688,0,-4096,-4096,0,0,0,0,180224,0,0,-8192,0,0,0,0,0,0,32768,32768,0,0,-8192,-8192,0,0,0,0,-131072,0,0,0,-6144,-6144,0,-7589888,0,3100672,0,0,0,0,77824,0,0,0,0,0,0,0,-10240,-10240,0,0,0,0,0,0,-36864,-36864,0,0
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,2,1,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1
[M3] rank=3 service=ts-admin-order-service metric=container.memory.usage baseline=693770410.666667 peak=701423616.0 signed_z=90.049 onset_bin=37 onset_rel_s=280.807 persistence_bins=27
values_compact=delta:693788672,0,114688,0,4096,4096,0,0,0,0,-180224,0,0,8192,0,0,0,0,0,0,-32768,-32768,0,0,8192,8192,0,0,0,0,131072,0,0,0,6144,6144,0,7589888,0,-3100672,0,0,0,0,-77824,0,0,0,0,0,0,0,10240,10240,0,0,0,0,0,0,36864,36864,0,0
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,2,1,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1
[M4] rank=4 service=ts-admin-order-service metric=container.memory.working_set baseline=693385386.666667 peak=701038592.0 signed_z=90.049 onset_bin=37 onset_rel_s=280.807 persistence_bins=27
values_compact=delta:693403648,0,114688,0,4096,4096,0,0,0,0,-180224,0,0,8192,0,0,0,0,0,0,-32768,-32768,0,0,8192,8192,0,0,0,0,131072,0,0,0,6144,6144,0,7589888,0,-3100672,0,0,0,0,-77824,0,0,0,0,0,0,0,10240,10240,0,0,0,0,0,0,36864,36864,0,0
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,2,1,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1
[M5] rank=5 service=ts-admin-order-service metric=k8s.pod.cpu.node.utilization baseline=4.2e-05 peak=0.000828 signed_z=87.548 onset_bin=39 onset_rel_s=295.783 persistence_bins=2
values_compact=delta:0.000033,0,0,0,0.000003,0.000002,-0.000002,-0.000003,0,0.000001,0,0.000002,0.000008,0.000009,-0.000008,-0.000007,0.000003,0.000003,0,0,-0.000002,0,0.000014,0.000008,0,-0.000018,-0.000001,-0.000001,0.000005,0.000005,-0.000008,-0.000008,0,-0.000004,-0.000001,-0.000002,0.000004,0.000004,0,0.000789,-0.000397,-0.000397,0,0,0,0.000012,0,-0.000003,0,0,0.000001,0,-0.000003,0.00001,0,-0.000004,0,-0.000002,0,0,-0.000008,0,0.000002,0.000001
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,2,1,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1
[M6] rank=6 service=ts-admin-order-service metric=k8s.pod.cpu.usage baseline=0.005433 peak=0.106011 signed_z=87.548 onset_bin=39 onset_rel_s=295.783 persistence_bins=2
values_compact=delta:0.004282,-0.000014,-0.000013,0,0.000317,0.000317,-0.000307,-0.000307,0,0.000072,0,0.000219,0.001125,0.001126,-0.001,-0.000999,0.000412,0.000411,-0.000028,-0.000029,-0.000167,0,0.001697,0.001046,0,-0.002297,-0.000138,-0.000138,0.000659,0.000659,-0.001002,-0.001002,0,-0.000509,-0.000207,-0.000208,0.000504,0.000504,0,0.101026,-0.050813,-0.050814,0,-0.000066,0,0.001535,0,-0.000339,0,0,0.00018,0,-0.000506,0.001355,0,-0.000467,0,-0.0003,0,0,-0.001007,0,0.000183,0.000184
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,2,1,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1
[M7] rank=7 service=ts-admin-order-service metric=k8s.pod.cpu_limit_utilization baseline=0.001087 peak=0.021202 signed_z=87.548 onset_bin=39 onset_rel_s=295.783 persistence_bins=2
values_compact=delta:0.000856,-0.000002,-0.000003,0,0.000063,0.000064,-0.000062,-0.000061,0,0.000014,0,0.000044,0.000225,0.000225,-0.0002,-0.000199,0.000082,0.000082,-0.000005,-0.000006,-0.000034,0,0.00034,0.000209,0,-0.000459,-0.000028,-0.000028,0.000132,0.000132,-0.0002,-0.000201,0,-0.000102,-0.000041,-0.000042,0.000101,0.000101,0,0.020205,-0.010162,-0.010163,0,-0.000013,0,0.000307,0,-0.000068,0,0,0.000036,0,-0.000101,0.000271,0,-0.000094,0,-0.00006,0,0,-0.000201,0,0.000036,0.000037
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,2,1,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1
[M8] rank=8 service=ts-admin-order-service metric=k8s.pod.memory.rss baseline=683162112.0 peak=687726592.0 signed_z=70.306 onset_bin=39 onset_rel_s=295.783 persistence_bins=25
values_compact=delta:683126784,59392,59392,0,6144,6144,0,0,0,0,0,-131072,4096,4096,0,0,0,0,0,0,0,0,-69632,20480,0,0,0,0,45056,45056,0,0,0,12288,0,0,-28672,-28672,0,4554752,0,0,0,0,0,-53248,0,0,0,0,0,0,0,12288,0,0,0,0,0,0,0,0,40960,40960
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,2,1,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1
[M9] rank=9 service=ts-admin-order-service metric=container.memory.rss baseline=683105536.0 peak=687685632.0 signed_z=70.054 onset_bin=37 onset_rel_s=280.807 persistence_bins=27
values_compact=delta:683085824,0,118784,0,6144,6144,0,0,0,0,-131072,0,0,8192,0,0,0,0,0,0,-34816,-34816,0,0,10240,10240,0,0,0,0,90112,0,0,0,6144,6144,0,4497408,0,0,0,0,0,0,-53248,0,0,0,0,0,0,0,6144,6144,0,0,0,0,0,0,40960,40960,0,0
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,2,1,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1
[M10] rank=10 service=ts-admin-order-service metric=k8s.pod.memory.node.utilization baseline=0.005143 peak=0.005177 signed_z=53.059 onset_bin=39 onset_rel_s=295.783 persistence_bins=25
values_compact=rle:0.005143*1,0.005144*10,0.005143*11,0.005142*6,0.005143*11,0.005177*6,0.005176*17,0.005177*2
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,2,1,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1
[M11] rank=11 service=ts-admin-order-service metric=k8s.pod.memory.available baseline=2527137109.333333 peak=2522587136.0 signed_z=-53.059 onset_bin=39 onset_rel_s=295.783 persistence_bins=25
values_compact=delta:2527137792,-57344,-57344,0,-4096,-4096,0,0,0,0,0,180224,-4096,-4096,0,0,0,0,0,0,0,0,65536,-16384,0,0,0,0,-65536,-65536,0,0,0,-12288,0,0,36864,36864,0,-4562944,0,0,0,0,0,77824,0,0,0,0,0,0,0,-20480,0,0,0,0,0,0,0,0,-36864,-36864
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,2,1,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1
[M12] rank=12 service=ts-admin-order-service metric=k8s.pod.memory_limit_utilization baseline=0.215593 peak=0.217005 signed_z=53.059 onset_bin=39 onset_rel_s=295.783 persistence_bins=25
values_compact=rle:0.215593*1,0.215611*1,0.215628*2,0.21563*1,0.215631*6,0.215575*1,0.215576*1,0.215577*9,0.215557*1,0.215562*5,0.215583*1,0.215603*4,0.215607*3,0.215595*1,0.215584*2,0.217*6,0.216976*8,0.216983*9,0.216994*1,0.217005*1
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,2,1,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[274.93790769577026,474.93360328674316]

=== LOG SUMMARY ===
{"entries":[{"error_logs":3460,"error_pct":19.25,"service":"ts-seat-service","total_logs":17978},{"error_logs":326,"error_pct":15.96,"service":"ts-food-service","total_logs":2043},{"error_logs":192,"error_pct":40.0,"service":"ts-notification-service","total_logs":480},{"error_logs":190,"error_pct":40.0,"service":"ts-delivery-service","total_logs":475},{"error_logs":126,"error_pct":5.6,"service":"ts-preserve-service","total_logs":2251},{"error_logs":126,"error_pct":1.91,"service":"ts-order-service","total_logs":6614},{"error_logs":55,"error_pct":6.87,"service":"ts-consign-service","total_logs":801},{"error_logs":17,"error_pct":100.0,"service":"mysql","total_logs":17}],"mode":"errors","omitted_services":24,"service_count":32}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":82499.0,"error_pct":47.58,"p95_during_ms":30010.03033745,"p95_pre_ms":36.332216600000024,"service":"ts-consign-service","spans":808},{"delta_pct":128.5,"error_pct":0.0,"p95_during_ms":12.587988,"p95_pre_ms":5.508199199999979,"service":"ts-order-service","spans":17490},{"delta_pct":112.1,"error_pct":0.0,"p95_during_ms":9.596740599999984,"p95_pre_ms":4.524259000000003,"service":"ts-train-service","spans":10881},{"delta_pct":111.1,"error_pct":0.0,"p95_during_ms":89.6968086,"p95_pre_ms":42.4913553,"service":"ts-inside-payment-service","spans":606},{"delta_pct":98.9,"error_pct":0.0,"p95_during_ms":36.46757659999999,"p95_pre_ms":18.336488999999972,"service":"ts-seat-service","spans":14349},{"delta_pct":89.0,"error_pct":0.0,"p95_during_ms":164.119406,"p95_pre_ms":86.8181054,"service":"ts-cancel-service","spans":18},{"delta_pct":88.0,"error_pct":0.0,"p95_during_ms":80.57175789999961,"p95_pre_ms":42.8638305,"service":"ts-food-service","spans":2160},{"delta_pct":83.3,"error_pct":0.0,"p95_during_ms":18.99149975,"p95_pre_ms":10.36096855,"service":"ts-assurance-service","spans":744}],"omitted_services":22,"service_count":30}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=35 omitted_edges=1
[{"evidence_source":"metric","onset_rel_s":259.2,"rank":1,"service":"ts-preserve-service","severity_z":12.071},{"evidence_source":"metric","onset_rel_s":280.2,"rank":2,"service":"ts-admin-order-service","severity_z":120.899},{"evidence_source":"trace","onset_rel_s":284.4,"rank":3,"service":"ts-consign-service","severity_z":3.748},{"evidence_source":"metric","onset_rel_s":310.8,"rank":4,"service":"mysql","severity_z":17.271},{"evidence_source":"trace","onset_rel_s":334.2,"rank":5,"service":"ts-verification-code-service","severity_z":394.629},{"evidence_source":"trace","onset_rel_s":344.4,"rank":6,"service":"ts-ui-dashboard","severity_z":13.139},{"evidence_source":"trace","onset_rel_s":344.4,"rank":7,"service":"loadgenerator","severity_z":13.138},{"evidence_source":"trace","onset_rel_s":354.6,"rank":8,"service":"ts-basic-service","severity_z":147.271},{"evidence_source":"metric","onset_rel_s":361.2,"rank":9,"service":"ts-price-service","severity_z":25.039},{"evidence_source":"metric","onset_rel_s":364.2,"rank":10,"service":"ts-voucher-service","severity_z":12.542},{"evidence_source":"trace","onset_rel_s":374.4,"rank":11,"service":"ts-order-service","severity_z":11.555},{"evidence_source":"trace","onset_rel_s":384.6,"rank":12,"service":"ts-train-service","severity_z":4.777},{"evidence_source":"trace","onset_rel_s":394.2,"rank":13,"service":"ts-seat-service","severity_z":12.449},{"evidence_source":"metric","onset_rel_s":396.0,"rank":14,"service":"ts-avatar-service","severity_z":11.975}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"ts-ui-dashboard","caller":"loadgenerator"},{"callee":"ts-price-service","caller":"ts-basic-service"},{"callee":"ts-train-service","caller":"ts-basic-service"},{"callee":"ts-basic-service","caller":"ts-preserve-service"},{"callee":"ts-order-service","caller":"ts-preserve-service"},{"callee":"ts-seat-service","caller":"ts-preserve-service"},{"callee":"ts-order-service","caller":"ts-seat-service"},{"callee":"ts-consign-service","caller":"ts-ui-dashboard"},{"callee":"ts-order-service","caller":"ts-ui-dashboard"},{"callee":"ts-preserve-service","caller":"ts-ui-dashboard"},{"callee":"ts-train-service","caller":"ts-ui-dashboard"},{"callee":"ts-verification-code-service","caller":"ts-ui-dashboard"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

[excluded before optimizer]

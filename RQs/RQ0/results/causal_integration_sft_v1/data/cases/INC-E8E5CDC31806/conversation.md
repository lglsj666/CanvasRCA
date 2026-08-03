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
opaque_id: INC-E8E5CDC31806
observation_window={"duration_rel_s":478.977,"source_metric_rows":952}
selection_summary={"candidate_count":104,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":901,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["loadgenerator","loadgenerator-d75cc479f-9478c","mysql","mysql-0","rabbitmq","rabbitmq-0","ts-admin-basic-info-service","ts-admin-basic-info-service-66cdcc94bc-std94","ts-admin-order-service","ts-admin-order-service-5b6dc77d7d-rfswn","ts-admin-route-service","ts-admin-route-service-f9c84f85f-fzhtf","ts-admin-travel-service","ts-admin-travel-service-659b5c9df4-zpjj2","ts-admin-user-service","ts-admin-user-service-5bfc8844b9-bxprf","ts-assurance-service","ts-assurance-service-75c854dc5c-tlqlm","ts-auth-service","ts-auth-service-69bdd5df8-q85dm","ts-avatar-service","ts-avatar-service-845b64df6-zctsw","ts-basic-service","ts-basic-service-7c6d59d5c4-8ls52","ts-cancel-service","ts-cancel-service-7ffd988fdb-wwt2b","ts-config-service","ts-config-service-55cffbf48b-wxppb","ts-consign-price-service","ts-consign-price-service-654cb4fc65-hx25p","ts-consign-service","ts-consign-service-9954fddf-56fj7","ts-contacts-service","ts-contacts-service-6d745b6c8f-pjd6t","ts-delivery-service","ts-delivery-service-694895c6cb-xx47j","ts-execute-service","ts-execute-service-8457c56cb7-ngg9j","ts-food-delivery-service","ts-food-delivery-service-96d856899-97lmx","ts-food-service","ts-food-service-64d454885b-mhqcq","ts-gateway-service","ts-gateway-service-7f988fb8c4-5v5n7","ts-inside-payment-service","ts-inside-payment-service-5ccb8ccb87-qc56l","ts-news-service","ts-news-service-6d6c6d7855-46hvm","ts-notification-service","ts-notification-service-58f6c468d7-xh6hn","ts-order-other-service","ts-order-other-service-5d6878687f-x549h","ts-order-service","ts-order-service-6794d6f564-stxpp","ts-payment-service","ts-payment-service-58854d694-qkfdr","ts-preserve-other-service","ts-preserve-other-service-64fd9c88cf-ltrqw","ts-preserve-service","ts-preserve-service-696df489d4-85sp4","ts-price-service","ts-price-service-67c895b45-lc5fp","ts-rebook-service","ts-rebook-service-7c7644bbdd-thldv","ts-route-plan-service","ts-route-plan-service-556cddc5c9-wxv7h","ts-route-service","ts-route-service-cfc6dbcf7-js5bc","ts-seat-service","ts-seat-service-6c78b7d797-z7rcb","ts-security-service","ts-security-service-55f5b777bb-kf8vb","ts-station-food-service","ts-station-food-service-746f6779d7-zwmr6","ts-station-service","ts-station-service-65986cc944-5cdr5","ts-ticket-office-service","ts-ticket-office-service-d7c58b8c7-8dcvj","ts-train-food-service","ts-train-food-service-d5485c677-w2v2k","ts-train-service","ts-train-service-9b56d75b6-jjhpn","ts-travel-plan-service","ts-travel-plan-service-7875c49896-wtzbp","ts-travel-service","ts-travel-service-c7b5c6d9b-p268k","ts-travel2-service","ts-travel2-service-7ff5bbbf54-qtgqr","ts-ui-dashboard","ts-ui-dashboard-57867cb85c-7pppb","ts-user-service","ts-user-service-54dd6b48c-vhhbk","ts-verification-code-service","ts-verification-code-service-85785c4f79-c74hr","ts-voucher-service","ts-voucher-service-689c4fc885-k8x9v","ts-wait-order-service","ts-wait-order-service-7cf6bc9468-xg7jt","worker1","worker2","worker3","worker4","worker5","worker6"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[3.742,11.226,18.71,26.194,33.678,41.162,48.646,56.13,63.614,71.098,78.582,86.066,93.55,101.034,108.518,116.002,123.486,130.97,138.454,145.938,153.422,160.906,168.39,175.875,183.359,190.843,198.327,205.811,213.295,220.779,228.263,235.747,243.231,250.715,258.199,265.683,273.167,280.651,288.135,295.619,303.103,310.587,318.071,325.555,333.039,340.523,348.007,355.491,362.975,370.459,377.943,385.427,392.911,400.395,407.879,415.363,422.847,430.331,437.815,445.299,452.783,460.267,467.751,475.235]
[M1] rank=1 service=ts-preserve-service metric=k8s.pod.memory.page_faults baseline=138152.583333 peak=147049.0 signed_z=32.215 onset_bin=36 onset_rel_s=273.167 persistence_bins=28
values_compact=delta:137760,0,0,22,0,34,0,6.5,6.5,43,43,0,243,0,0,37,0,47.5,47.5,34,34,13,13,7,7,18.5,18.5,16.5,16.5,23,23,30,30,0,48,0,452,0,108,2.5,2.5,14,14,3.5,3.5,41,41,0,38,0,7496,0,7,12,12,0,22,0,37,0,102,0,0,9.5
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M2] rank=2 service=ts-preserve-service metric=container.memory.page_faults baseline=137369.979167 peak=146264.0 signed_z=32.046 onset_bin=37 onset_rel_s=280.651 persistence_bins=27
values_compact=delta:136974,2.5,2.5,20,0,16.5,16.5,0,29,32.5,32.5,0,247,0,27,0,49,32.5,32.5,0,64,0,28,0,0,44,32,0,0,33,23,0,0,98,0,151.5,151.5,122.5,122.5,14,0,15.5,15.5,5,0,84,0,19.5,19.5,7489,7,0,0,27,0,25,0,18.5,18.5,102,0,0.5,0.5,9.5
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M3] rank=3 service=ts-cancel-service metric=k8s.pod.cpu_limit_utilization baseline=0.001586 peak=0.033991 signed_z=31.951 onset_bin=62 onset_rel_s=467.751 persistence_bins=2
values_compact=delta:0.001327,0.000013,0.000012,0.003027,0,-0.001492,-0.001492,0,0.001835,-0.001153,-0.001153,-0.000006,-0.000006,0,0.000185,0,-0.00016,0,0,0.000055,0,0.000208,0,-0.000138,0,0.000278,0,-0.000101,0.000146,0,0,0.001604,-0.001667,0,-0.000068,0.000019,0.00002,0,-0.000054,0,-0.000213,0,-0.000048,0,0.000011,0,0,0.000264,-0.000116,-0.000044,-0.000044,0,0.000154,0,0.000212,-0.000112,-0.000113,-0.000018,-0.000018,-0.000088,-0.000088,0,0.033013,0
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,2
[M4] rank=4 service=ts-cancel-service metric=k8s.pod.cpu.node.utilization baseline=6.2e-05 peak=0.001328 signed_z=31.951 onset_bin=62 onset_rel_s=467.751 persistence_bins=2
values_compact=delta:0.000052,0,0.000001,0.000118,0,-0.000058,-0.000059,0,0.000072,-0.000045,-0.000045,0,0,0,0.000007,0,-0.000006,0,0,0.000002,0,0.000008,0,-0.000006,0,0.000011,0,-0.000004,0.000006,0,0,0.000063,-0.000065,0,-0.000003,0.000001,0.000001,0,-0.000003,0,-0.000008,0,-0.000002,0,0.000001,0,0,0.00001,-0.000005,-0.000001,-0.000002,0,0.000006,0,0.000008,-0.000004,-0.000004,-0.000001,-0.000001,-0.000003,-0.000004,0,0.00129,0
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,2
[M5] rank=5 service=ts-cancel-service metric=k8s.pod.cpu.usage baseline=0.007932 peak=0.169957 signed_z=31.951 onset_bin=62 onset_rel_s=467.751 persistence_bins=2
values_compact=delta:0.006633,0.000065,0.000064,0.015131,0,-0.00746,-0.00746,0,0.009176,-0.005765,-0.005766,-0.00003,-0.000029,0,0.000927,0,-0.0008,0,0,0.000276,0,0.001039,0,-0.000691,0,0.001388,0,-0.000505,0.000733,0,0,0.008019,-0.008333,0,-0.000342,0.000097,0.000098,0,-0.000271,0,-0.001063,0,-0.00024,0,0.000056,0,0,0.001316,-0.00058,-0.00022,-0.00022,0,0.000771,0,0.001062,-0.000562,-0.000562,-0.000091,-0.000091,-0.00044,-0.00044,0,0.165067,0
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,2
[M6] rank=6 service=ts-preserve-service metric=k8s.pod.memory.rss baseline=753572778.666667 peak=778969088.0 signed_z=27.622 onset_bin=36 onset_rel_s=273.167 persistence_bins=28
values_compact=delta:752254976,0,0,77824,0,114688,0,-10240,-10240,163840,163840,0,901120,0,0,151552,0,182272,182272,57344,57344,40960,40960,8192,8192,16384,16384,53248,53248,94208,94208,110592,110592,0,192512,0,1830912,0,417792,8192,8192,51200,51200,6144,6144,157696,157696,0,53248,0,21094400,0,-11800576,2048,2048,0,77824,0,147456,0,397312,0,0,26624
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M7] rank=7 service=ts-cancel-service metric=container.cpu.usage baseline=0.008174 peak=0.153986 signed_z=27.276 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.007226,-0.000242,-0.000242,0.0059,0.005899,-0.005704,-0.005705,-0.001387,0.017561,0,-0.018706,0,0,0.000821,-0.000737,0,0,0.000025,0,0.000288,0.000454,0,0.000154,0.000096,0.000097,0.000565,0.000566,-0.000286,0,0.003688,0.003688,-0.003601,-0.003601,-0.000256,-0.000256,0.000272,0,0.00004,0,-0.000714,-0.000714,0.000048,0.000047,-0.000159,-0.000158,0.000645,0.000646,-0.000464,-0.000464,0.00029,-0.000084,0.000231,0.000231,0,0.00089,0,-0.000876,0,0,-0.000812,0,0.001044,0,0.073871
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,2
[M8] rank=8 service=ts-preserve-service metric=k8s.pod.memory.available baseline=2456267861.333333 peak=2430976000.0 signed_z=-26.869 onset_bin=36 onset_rel_s=273.167 persistence_bins=28
values_compact=delta:2457702400,0,0,-86016,0,-94208,0,-108544,-108544,-149504,-149504,0,-1196032,0,0,122880,0,-49152,-49152,-73728,-73728,-292864,-292864,249856,249856,-30720,-30720,-43008,-43008,-100352,-100352,-233472,-233472,0,61440,0,-1830912,0,-1187840,376832,376832,-45056,-45056,-6144,-6144,-161792,-161792,0,-323584,0,-20856832,0,11784192,-2048,-2048,0,-331776,0,81920,0,-389120,4096,4096,-28672
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M9] rank=9 service=ts-preserve-service metric=k8s.pod.memory.node.utilization baseline=0.005668 peak=0.005855 signed_z=26.869 onset_bin=36 onset_rel_s=273.167 persistence_bins=28
values_compact=rle:0.005657*3,0.005658*2,0.005659*3,0.00566*1,0.005661*1,0.005662*2,0.005671*3,0.00567*2,0.005671*2,0.005672*2,0.005674*1,0.005677*1,0.005675*1,0.005673*3,0.005674*2,0.005675*2,0.005677*1,0.005679*2,0.005678*2,0.005692*2,0.005701*1,0.005698*1,0.005695*1,0.005696*4,0.005697*1,0.005698*2,0.005701*2,0.005855*2,0.005768*4,0.00577*4,0.005773*4
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M10] rank=10 service=ts-preserve-service metric=k8s.pod.memory.usage baseline=765342634.666667 peak=790634496.0 signed_z=26.869 onset_bin=36 onset_rel_s=273.167 persistence_bins=28
values_compact=delta:763908096,0,0,86016,0,94208,0,108544,108544,149504,149504,0,1196032,0,0,-122880,0,49152,49152,73728,73728,292864,292864,-249856,-249856,30720,30720,43008,43008,100352,100352,233472,233472,0,-61440,0,1830912,0,1187840,-376832,-376832,45056,45056,6144,6144,161792,161792,0,323584,0,20856832,0,-11784192,2048,2048,0,331776,0,-81920,0,389120,-4096,-4096,28672
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M11] rank=11 service=ts-preserve-service metric=k8s.pod.memory.working_set baseline=764957610.666667 peak=790249472.0 signed_z=26.869 onset_bin=36 onset_rel_s=273.167 persistence_bins=28
values_compact=delta:763523072,0,0,86016,0,94208,0,108544,108544,149504,149504,0,1196032,0,0,-122880,0,49152,49152,73728,73728,292864,292864,-249856,-249856,30720,30720,43008,43008,100352,100352,233472,233472,0,-61440,0,1830912,0,1187840,-376832,-376832,45056,45056,6144,6144,161792,161792,0,323584,0,20856832,0,-11784192,2048,2048,0,331776,0,-81920,0,389120,-4096,-4096,28672
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M12] rank=12 service=ts-preserve-service metric=k8s.pod.memory_limit_utilization baseline=0.237594 peak=0.245445 signed_z=26.869 onset_bin=36 onset_rel_s=273.167 persistence_bins=28
values_compact=delta:0.237148,0,0,0.000027,0,0.000029,0,0.000034,0.000034,0.000046,0.000046,0,0.000372,0,0,-0.000038,0,0.000015,0.000015,0.000023,0.000023,0.000091,0.000091,-0.000078,-0.000077,0.000009,0.00001,0.000013,0.000013,0.000032,0.000031,0.000072,0.000073,0,-0.000019,0,0.000568,0,0.000369,-0.000117,-0.000117,0.000014,0.000014,0.000002,0.000002,0.00005,0.00005,0,0.0001,0,0.006475,0,-0.003658,0.000001,0,0,0.000103,0,-0.000025,0,0.000121,-0.000002,-0.000001,0.000009
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[362.8885848522186,477.89087104797363]

=== LOG SUMMARY ===
{"entries":[{"error_logs":3856,"error_pct":19.29,"service":"ts-seat-service","total_logs":19987},{"error_logs":387,"error_pct":16.68,"service":"ts-food-service","total_logs":2320},{"error_logs":137,"error_pct":5.88,"service":"ts-preserve-service","total_logs":2329},{"error_logs":137,"error_pct":1.95,"service":"ts-order-service","total_logs":7030},{"error_logs":96,"error_pct":25.0,"service":"ts-notification-service","total_logs":384},{"error_logs":95,"error_pct":25.0,"service":"ts-delivery-service","total_logs":380},{"error_logs":14,"error_pct":0.88,"service":"ts-travel-plan-service","total_logs":1593},{"error_logs":14,"error_pct":0.16,"service":"ts-ui-dashboard","total_logs":8744}],"mode":"errors","omitted_services":23,"service_count":31}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":1748.2,"error_pct":0.0,"p95_during_ms":13578.703024,"p95_pre_ms":734.7020172999966,"service":"ts-travel-plan-service","spans":2811},{"delta_pct":367.5,"error_pct":0.0,"p95_during_ms":530.9823898,"p95_pre_ms":113.58891199999998,"service":"ts-cancel-service","spans":36},{"delta_pct":266.1,"error_pct":0.83,"p95_during_ms":5542.439735450079,"p95_pre_ms":1514.1110582999959,"service":"ts-route-plan-service","spans":2184},{"delta_pct":244.5,"error_pct":0.0,"p95_during_ms":22.062107399999988,"p95_pre_ms":6.4043871999999995,"service":"ts-train-food-service","spans":2829},{"delta_pct":216.1,"error_pct":0.0,"p95_during_ms":17.178956399999997,"p95_pre_ms":5.434808299999997,"service":"ts-order-other-service","spans":11695},{"delta_pct":78.7,"error_pct":0.0,"p95_during_ms":39.08278949999998,"p95_pre_ms":21.86458985000001,"service":"ts-payment-service","spans":345},{"delta_pct":70.2,"error_pct":0.0,"p95_during_ms":17.471584499999683,"p95_pre_ms":10.2643402,"service":"ts-station-food-service","spans":1868},{"delta_pct":64.2,"error_pct":0.0,"p95_during_ms":13.009345299999952,"p95_pre_ms":7.92330459999999,"service":"ts-contacts-service","spans":3670}],"omitted_services":22,"service_count":30}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=35 omitted_edges=0
[{"evidence_source":"metric","onset_rel_s":251.4,"rank":1,"service":"ts-food-service","severity_z":18.356},{"evidence_source":"metric","onset_rel_s":270.6,"rank":2,"service":"ts-security-service","severity_z":23.114},{"evidence_source":"metric","onset_rel_s":272.4,"rank":3,"service":"ts-config-service","severity_z":11.898},{"evidence_source":"metric","onset_rel_s":272.4,"rank":4,"service":"ts-gateway-service","severity_z":10.237},{"evidence_source":"metric","onset_rel_s":286.2,"rank":5,"service":"ts-contacts-service","severity_z":11.148},{"evidence_source":"metric","onset_rel_s":378.0,"rank":6,"service":"ts-preserve-service","severity_z":32.215},{"evidence_source":"metric","onset_rel_s":396.6,"rank":7,"service":"ts-avatar-service","severity_z":11.874},{"evidence_source":"trace","onset_rel_s":404.4,"rank":8,"service":"ts-route-plan-service","severity_z":4.81},{"evidence_source":"trace","onset_rel_s":463.8,"rank":9,"service":"ts-cancel-service","severity_z":30.582},{"evidence_source":"metric","onset_rel_s":471.6,"rank":10,"service":"ts-consign-service","severity_z":13.059},{"evidence_source":"none","onset_rel_s":null,"rank":11,"service":"ts-preserve-other-service","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":12,"service":"rabbitmq","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":13,"service":"ts-route-service","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":14,"service":"ts-order-service","severity_z":0.0}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"ts-order-service","caller":"ts-cancel-service"},{"callee":"ts-contacts-service","caller":"ts-preserve-service"},{"callee":"ts-food-service","caller":"ts-preserve-service"},{"callee":"ts-order-service","caller":"ts-preserve-service"},{"callee":"ts-security-service","caller":"ts-preserve-service"},{"callee":"ts-route-service","caller":"ts-route-plan-service"},{"callee":"ts-order-service","caller":"ts-security-service"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

[excluded before optimizer]

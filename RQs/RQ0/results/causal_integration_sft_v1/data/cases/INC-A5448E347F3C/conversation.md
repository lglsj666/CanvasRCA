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
opaque_id: INC-A5448E347F3C
observation_window={"duration_rel_s":477.338,"source_metric_rows":952}
selection_summary={"candidate_count":104,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":900,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["loadgenerator","loadgenerator-76c5949c78-xghgj","mysql","mysql-0","rabbitmq","rabbitmq-0","ts-admin-basic-info-service","ts-admin-basic-info-service-579bc4cd8d-bbgq6","ts-admin-order-service","ts-admin-order-service-76fc4c68d5-hdxr8","ts-admin-route-service","ts-admin-route-service-85bffd5f6-6qvrv","ts-admin-travel-service","ts-admin-travel-service-797ccbcff7-7t2jw","ts-admin-user-service","ts-admin-user-service-7874ccc7c4-65rmg","ts-assurance-service","ts-assurance-service-d87bf675d-j9wjw","ts-auth-service","ts-auth-service-6477f4967c-mmzw7","ts-avatar-service","ts-avatar-service-74fd5ff4c7-l2cwl","ts-basic-service","ts-basic-service-59f887c7d5-nw9h9","ts-cancel-service","ts-cancel-service-67454d8789-s9h9m","ts-config-service","ts-config-service-56457f8db5-8sw2z","ts-consign-price-service","ts-consign-price-service-54b69c6854-w2vfz","ts-consign-service","ts-consign-service-686f9c998-d2rcm","ts-contacts-service","ts-contacts-service-7df9fc84b6-47hw8","ts-delivery-service","ts-delivery-service-55b55bb555-68z22","ts-execute-service","ts-execute-service-64b744d564-wb7cz","ts-food-delivery-service","ts-food-delivery-service-599dfbdb6d-z9j7g","ts-food-service","ts-food-service-755696bb9f-8zlff","ts-gateway-service","ts-gateway-service-9cdfbbdfc-rc97c","ts-inside-payment-service","ts-inside-payment-service-7666f6c64d-ptd4r","ts-news-service","ts-news-service-7869d45c45-r5fb5","ts-notification-service","ts-notification-service-b5b74bb44-f9gw2","ts-order-other-service","ts-order-other-service-67cbddcb88-qz4wv","ts-order-service","ts-order-service-85b9979d59-vtln5","ts-payment-service","ts-payment-service-5df5775665-fwxw4","ts-preserve-other-service","ts-preserve-other-service-74f69f9db4-c5h2g","ts-preserve-service","ts-preserve-service-7f8d678dcf-p6tnx","ts-price-service","ts-price-service-c4b84c894-twhnz","ts-rebook-service","ts-rebook-service-776674d89f-lrtms","ts-route-plan-service","ts-route-plan-service-7f4b79f79b-dg6pm","ts-route-service","ts-route-service-6db4bdfd5d-mt8st","ts-seat-service","ts-seat-service-5dddf49dfd-phs2h","ts-security-service","ts-security-service-69797c9fdf-nmgv4","ts-station-food-service","ts-station-food-service-6c88c88456-87r78","ts-station-service","ts-station-service-75dc8bb94c-8knkv","ts-ticket-office-service","ts-ticket-office-service-7cd6fff84-848zt","ts-train-food-service","ts-train-food-service-5cb6b7d98b-hvd74","ts-train-service","ts-train-service-6ccc6f4465-lxlzp","ts-travel-plan-service","ts-travel-plan-service-56754fc8bc-w4bpc","ts-travel-service","ts-travel-service-5577469b95-t7bnn","ts-travel2-service","ts-travel2-service-859b87cf49-s42b6","ts-ui-dashboard","ts-ui-dashboard-897fdb6b4-z4bwj","ts-user-service","ts-user-service-7fdd6fdfb8-mzpqb","ts-verification-code-service","ts-verification-code-service-5795bcf896-fj7dx","ts-voucher-service","ts-voucher-service-6db9df749b-bk49z","ts-wait-order-service","ts-wait-order-service-5b9fcd797f-666cg","worker1","worker2","worker3","worker4","worker5","worker6"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[3.729,11.188,18.646,26.104,33.563,41.021,48.48,55.938,63.396,70.855,78.313,85.772,93.23,100.689,108.147,115.605,123.064,130.522,137.981,145.439,152.897,160.356,167.814,175.273,182.731,190.189,197.648,205.106,212.565,220.023,227.481,234.94,242.398,249.857,257.315,264.774,272.232,279.69,287.149,294.607,302.066,309.524,316.982,324.441,331.899,339.358,346.816,354.274,361.733,369.191,376.65,384.108,391.566,399.025,406.483,413.942,421.4,428.858,436.317,443.775,451.234,458.692,466.151,473.609]
[M1] rank=1 service=ts-consign-service metric=k8s.pod.cpu_limit_utilization baseline=0.004241 peak=0.338391 signed_z=95.548 onset_bin=13 onset_rel_s=100.689 persistence_bins=5
values_compact=delta:0.004019,-0.000873,0,0,0.000921,-0.001203,0,0,0.002179,0.001959,0,0,-0.00333,0.011243,0,0,-0.012664,0,0.000271,0.00019,0.000191,-0.000491,-0.00049,0,0.00112,0,-0.001445,0,0.000688,0,0,0.001229,-0.000748,0,-0.000873,0.00155,0.001549,0,-0.00172,0,-0.002188,0,0.000645,0.000139,0.000138,-0.000216,-0.000216,0.336817,0,-0.335282,0.001232,0,-0.003057,0,0.000907,0,-0.000327,0,0.002666,0,-0.002689,0,-0.000353,-0.000072
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M2] rank=2 service=ts-consign-service metric=k8s.pod.cpu.node.utilization baseline=0.000166 peak=0.013218 signed_z=95.548 onset_bin=13 onset_rel_s=100.689 persistence_bins=5
values_compact=delta:0.000157,-0.000034,0,0,0.000036,-0.000047,0,0,0.000085,0.000077,0,0,-0.000131,0.00044,0,0,-0.000495,0,0.00001,0.000008,0.000007,-0.000019,-0.000019,0,0.000044,0,-0.000057,0,0.000027,0,0,0.000048,-0.000029,0,-0.000034,0.00006,0.000061,0,-0.000067,0,-0.000086,0,0.000026,0.000005,0.000005,-0.000008,-0.000009,0.013157,0,-0.013097,0.000049,0,-0.00012,0,0.000036,0,-0.000013,0,0.000104,0,-0.000105,0,-0.000014,-0.000003
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M3] rank=3 service=ts-consign-service metric=k8s.pod.cpu.usage baseline=0.021207 peak=1.691956 signed_z=95.548 onset_bin=13 onset_rel_s=100.689 persistence_bins=5
values_compact=delta:0.020097,-0.004366,0,0,0.004602,-0.006011,0,0,0.010895,0.009792,0,0,-0.016651,0.056219,0,0,-0.063324,0,0.001355,0.000953,0.000953,-0.002452,-0.002453,0,0.0056,0,-0.007224,0,0.003438,0,0,0.006149,-0.00374,0,-0.004365,0.007746,0.007746,0,-0.008599,0,-0.01094,0,0.003227,0.000692,0.000692,-0.001082,-0.001081,1.684088,0,-1.676409,0.00616,0,-0.015289,0,0.004538,0,-0.001636,0,0.013331,0,-0.013447,0,-0.001766,-0.000358
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M4] rank=4 service=ts-consign-service metric=container.cpu.usage baseline=0.018843 peak=0.951375 signed_z=88.379 onset_bin=48 onset_rel_s=361.733 persistence_bins=2
values_compact=delta:0.023004,0,-0.009012,0,0.002543,0.002543,-0.006636,0,0.010595,0.010594,-0.004455,-0.004455,0.010507,0.010508,0,-0.011449,-0.011449,-0.004929,-0.004929,-0.001477,-0.001477,0,0.00155,0,0.006474,0,-0.010991,0,0,0.003552,0,0.007911,0,-0.002364,-0.002364,0.001418,0.001418,0,0.0005,0,-0.011816,0,0.00422,-0.000048,-0.000047,-0.000635,-0.000635,0,0.943206,-0.462144,-0.462144,-0.008518,-0.008518,-0.000418,-0.000418,-0.000445,0,0.001286,0.001286,0.019445,0,-0.023136,0,0.000073
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M5] rank=5 service=ts-user-service metric=container.cpu.usage baseline=0.068542 peak=1.471875 signed_z=26.442 onset_bin=44 onset_rel_s=331.899 persistence_bins=2
values_compact=delta:0.060851,-0.024944,-0.011648,0,0.041735,-0.000972,0,0,-0.035905,0.079172,0.079173,-0.138626,0,-0.006915,-0.006914,0,-0.01401,0,-0.000188,0,0.071444,0,0.029377,0,0,0.064729,0,-0.151545,0,0.001704,0.001705,0.010235,0.010234,-0.025161,-0.025161,0.003673,0.003674,0,-0.000196,0.000426,0.000426,0.001387,0.001387,-0.006407,1.459135,0,-1.457075,0,0.006358,0,0.003322,0,-0.005933,0,0.015099,0,0,-0.00797,-0.000629,0,0,-0.011334,0,0.000892
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,1,2,2,1,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M6] rank=6 service=mysql metric=container.filesystem.available baseline=12492388522.666666 peak=13005819904.0 signed_z=24.042 onset_bin=41 onset_rel_s=309.524 persistence_bins=23
values_compact=delta:12514254848,-9576448,-585728,-585728,-1118208,-1191936,-602112,-602112,41512960,-78008320,20267008,20267008,-434176,-2605056,0,-528384,-19501056,-23068672,-23068672,54145024,-638976,-1329152,-1329152,-9560064,-8732672,0,-8765440,23091200,23091200,-557056,-708608,-1675264,-1675264,-569344,-9056256,-374784,-374784,-43098112,-47722496,37093376,37093376,216879104,104239104,105764864,105764864,-258048,-294912,-163840,-163840,-454656,0,-10416128,-385024,-253952,-253952,-417792,-17362944,-366592,-366592,-811008,-9101312,-440320,-440320,-897024
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M7] rank=7 service=mysql metric=k8s.pod.filesystem.available baseline=12492388522.666666 peak=13005819904.0 signed_z=24.042 onset_bin=41 onset_rel_s=309.524 persistence_bins=23
values_compact=delta:12514254848,-9576448,-585728,-585728,-1118208,-1191936,-602112,-602112,41512960,-78008320,20267008,20267008,-434176,-2605056,0,-528384,-19501056,-23068672,-23068672,54145024,-638976,-1329152,-1329152,-9560064,-8732672,0,-8765440,23091200,23091200,-557056,-708608,-1675264,-1675264,-569344,-9056256,-374784,-374784,-43098112,-47722496,37093376,37093376,216879104,104239104,105764864,105764864,-258048,-294912,-163840,-163840,-454656,0,-10416128,-385024,-253952,-253952,-417792,-17362944,-366592,-366592,-811008,-9101312,-440320,-440320,-897024
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M8] rank=8 service=ts-auth-service metric=container.filesystem.available baseline=12492388522.666666 peak=13005819904.0 signed_z=24.042 onset_bin=41 onset_rel_s=309.524 persistence_bins=23
values_compact=delta:12514254848,-9576448,-585728,-585728,-1118208,-1191936,-602112,-602112,41512960,-78008320,20267008,20267008,-434176,-2605056,0,-528384,-19501056,-23068672,-23068672,54145024,-638976,-1329152,-1329152,-9560064,-8732672,0,-8765440,23091200,23091200,-557056,-708608,-1675264,-1675264,-569344,-9056256,-374784,-374784,-43098112,-47722496,37093376,37093376,216879104,104239104,105764864,105764864,-258048,-294912,-163840,-163840,-454656,0,-10416128,-385024,-253952,-253952,-417792,-17362944,-366592,-366592,-811008,-9101312,-440320,-440320,-897024
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M9] rank=9 service=ts-auth-service metric=k8s.pod.filesystem.available baseline=12492388522.666666 peak=13005819904.0 signed_z=24.042 onset_bin=41 onset_rel_s=309.524 persistence_bins=23
values_compact=delta:12514254848,-9576448,-585728,-585728,-1118208,-1191936,-602112,-602112,41512960,-78008320,20267008,20267008,-434176,-2605056,0,-528384,-19501056,-23068672,-23068672,54145024,-638976,-1329152,-1329152,-9560064,-8732672,0,-8765440,23091200,23091200,-557056,-708608,-1675264,-1675264,-569344,-9056256,-374784,-374784,-43098112,-47722496,37093376,37093376,216879104,104239104,105764864,105764864,-258048,-294912,-163840,-163840,-454656,0,-10416128,-385024,-253952,-253952,-417792,-17362944,-366592,-366592,-811008,-9101312,-440320,-440320,-897024
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M10] rank=10 service=ts-consign-price-service metric=container.filesystem.available baseline=12492388522.666666 peak=13005819904.0 signed_z=24.042 onset_bin=41 onset_rel_s=309.524 persistence_bins=23
values_compact=delta:12514254848,-9576448,-585728,-585728,-1118208,-1191936,-602112,-602112,41512960,-78008320,20267008,20267008,-434176,-2605056,0,-528384,-19501056,-23068672,-23068672,54145024,-638976,-1329152,-1329152,-9560064,-8732672,0,-8765440,23091200,23091200,-557056,-708608,-1675264,-1675264,-569344,-9056256,-374784,-374784,-43098112,-47722496,37093376,37093376,216879104,104239104,105764864,105764864,-258048,-294912,-163840,-163840,-454656,0,-10416128,-385024,-253952,-253952,-417792,-17362944,-366592,-366592,-811008,-9101312,-440320,-440320,-897024
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M11] rank=11 service=ts-consign-price-service metric=k8s.pod.filesystem.available baseline=12492388522.666666 peak=13005819904.0 signed_z=24.042 onset_bin=41 onset_rel_s=309.524 persistence_bins=23
values_compact=delta:12514254848,-9576448,-585728,-585728,-1118208,-1191936,-602112,-602112,41512960,-78008320,20267008,20267008,-434176,-2605056,0,-528384,-19501056,-23068672,-23068672,54145024,-638976,-1329152,-1329152,-9560064,-8732672,0,-8765440,23091200,23091200,-557056,-708608,-1675264,-1675264,-569344,-9056256,-374784,-374784,-43098112,-47722496,37093376,37093376,216879104,104239104,105764864,105764864,-258048,-294912,-163840,-163840,-454656,0,-10416128,-385024,-253952,-253952,-417792,-17362944,-366592,-366592,-811008,-9101312,-440320,-440320,-897024
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M12] rank=12 service=ts-consign-service metric=container.filesystem.available baseline=12492388522.666666 peak=13005819904.0 signed_z=24.042 onset_bin=41 onset_rel_s=309.524 persistence_bins=23
values_compact=delta:12514254848,-9576448,-585728,-585728,-1118208,-1191936,-602112,-602112,41512960,-78008320,20267008,20267008,-434176,-2605056,0,-528384,-19501056,-23068672,-23068672,54145024,-638976,-1329152,-1329152,-9560064,-8732672,0,-8765440,23091200,23091200,-557056,-708608,-1675264,-1675264,-569344,-9056256,-374784,-374784,-43098112,-47722496,37093376,37093376,216879104,104239104,105764864,105764864,-258048,-294912,-163840,-163840,-454656,0,-10416128,-385024,-253952,-253952,-417792,-17362944,-366592,-366592,-811008,-9101312,-440320,-440320,-897024
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[347.19591665267944,367.28661608695984]

=== LOG SUMMARY ===
{"entries":[{"error_logs":3161,"error_pct":19.29,"service":"ts-seat-service","total_logs":16385},{"error_logs":366,"error_pct":17.43,"service":"ts-food-service","total_logs":2100},{"error_logs":134,"error_pct":1.64,"service":"ts-ui-dashboard","total_logs":8167},{"error_logs":104,"error_pct":5.32,"service":"ts-preserve-service","total_logs":1954},{"error_logs":104,"error_pct":1.77,"service":"ts-order-service","total_logs":5868},{"error_logs":66,"error_pct":25.19,"service":"ts-delivery-service","total_logs":262},{"error_logs":66,"error_pct":25.0,"service":"ts-notification-service","total_logs":264}],"mode":"errors","omitted_services":24,"service_count":31}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":683.9,"error_pct":0.0,"p95_during_ms":45.979522699999976,"p95_pre_ms":5.865199699999986,"service":"ts-train-service","spans":10438},{"delta_pct":629.5,"error_pct":0.0,"p95_during_ms":36.02336169999998,"p95_pre_ms":4.938423899999999,"service":"ts-station-service","spans":7775},{"delta_pct":474.8,"error_pct":0.0,"p95_during_ms":30.008955299999947,"p95_pre_ms":5.220628250000001,"service":"ts-price-service","spans":4475},{"delta_pct":365.5,"error_pct":0.0,"p95_during_ms":27.223670500000004,"p95_pre_ms":5.8482265,"service":"ts-config-service","spans":15810},{"delta_pct":324.7,"error_pct":0.0,"p95_during_ms":36.14839114999999,"p95_pre_ms":8.510933399999997,"service":"ts-order-service","spans":15535},{"delta_pct":316.5,"error_pct":0.0,"p95_during_ms":40.26777389999999,"p95_pre_ms":9.668786049999996,"service":"ts-contacts-service","spans":3199},{"delta_pct":300.9,"error_pct":0.0,"p95_during_ms":182.137404,"p95_pre_ms":45.42713750000001,"service":"ts-inside-payment-service","spans":594},{"delta_pct":279.7,"error_pct":0.0,"p95_during_ms":2891.697711,"p95_pre_ms":761.5816450499998,"service":"ts-travel-plan-service","spans":2265}],"omitted_services":22,"service_count":30}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=35 omitted_edges=0
[{"evidence_source":"metric","onset_rel_s":316.8,"rank":1,"service":"mysql","severity_z":24.042},{"evidence_source":"metric","onset_rel_s":316.8,"rank":2,"service":"ts-auth-service","severity_z":24.042},{"evidence_source":"metric","onset_rel_s":316.8,"rank":3,"service":"ts-consign-price-service","severity_z":24.042},{"evidence_source":"metric","onset_rel_s":316.8,"rank":4,"service":"ts-news-service","severity_z":24.042},{"evidence_source":"metric","onset_rel_s":316.8,"rank":5,"service":"ts-notification-service","severity_z":24.042},{"evidence_source":"metric","onset_rel_s":316.8,"rank":6,"service":"ts-travel-plan-service","severity_z":24.042},{"evidence_source":"metric","onset_rel_s":316.8,"rank":7,"service":"ts-voucher-service","severity_z":24.042},{"evidence_source":"metric","onset_rel_s":332.4,"rank":8,"service":"ts-user-service","severity_z":26.442},{"evidence_source":"metric","onset_rel_s":352.2,"rank":9,"service":"ts-consign-service","severity_z":95.548},{"evidence_source":"trace","onset_rel_s":352.8,"rank":10,"service":"ts-station-service","severity_z":3.629},{"evidence_source":"trace","onset_rel_s":363.0,"rank":11,"service":"ts-price-service","severity_z":6.897},{"evidence_source":"trace","onset_rel_s":382.8,"rank":12,"service":"ts-payment-service","severity_z":3.292},{"evidence_source":"trace","onset_rel_s":402.6,"rank":13,"service":"ts-order-service","severity_z":208.252},{"evidence_source":"metric","onset_rel_s":467.4,"rank":14,"service":"ts-config-service","severity_z":22.776}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"ts-consign-price-service","caller":"ts-consign-service"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

[excluded before optimizer]

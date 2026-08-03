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
opaque_id: INC-DA71F4982610
observation_window={"duration_rel_s":477.259,"source_metric_rows":952}
selection_summary={"candidate_count":104,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":901,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["loadgenerator","loadgenerator-567fdbd647-llk2p","mysql","mysql-0","rabbitmq","rabbitmq-0","ts-admin-basic-info-service","ts-admin-basic-info-service-579bc4cd8d-2x8bs","ts-admin-order-service","ts-admin-order-service-76fc4c68d5-kmjx2","ts-admin-route-service","ts-admin-route-service-85bffd5f6-2zk6j","ts-admin-travel-service","ts-admin-travel-service-797ccbcff7-vf4nb","ts-admin-user-service","ts-admin-user-service-7874ccc7c4-gzq4b","ts-assurance-service","ts-assurance-service-d87bf675d-ghfn6","ts-auth-service","ts-auth-service-6477f4967c-n48pr","ts-avatar-service","ts-avatar-service-74fd5ff4c7-mrdbc","ts-basic-service","ts-basic-service-59f887c7d5-s86np","ts-cancel-service","ts-cancel-service-67454d8789-zrn68","ts-config-service","ts-config-service-56457f8db5-6cmvk","ts-consign-price-service","ts-consign-price-service-54b69c6854-qxqrz","ts-consign-service","ts-consign-service-686f9c998-dgp7j","ts-contacts-service","ts-contacts-service-7df9fc84b6-58frs","ts-delivery-service","ts-delivery-service-55b55bb555-dr2nl","ts-execute-service","ts-execute-service-64b744d564-j99r7","ts-food-delivery-service","ts-food-delivery-service-599dfbdb6d-7rljq","ts-food-service","ts-food-service-755696bb9f-js7f4","ts-gateway-service","ts-gateway-service-9cdfbbdfc-x96cs","ts-inside-payment-service","ts-inside-payment-service-7666f6c64d-jhkvm","ts-news-service","ts-news-service-7869d45c45-qzd27","ts-notification-service","ts-notification-service-b5b74bb44-cztjw","ts-order-other-service","ts-order-other-service-67cbddcb88-qmdpj","ts-order-service","ts-order-service-85b9979d59-sd8nn","ts-payment-service","ts-payment-service-5df5775665-d9st7","ts-preserve-other-service","ts-preserve-other-service-74f69f9db4-7nbfz","ts-preserve-service","ts-preserve-service-7f8d678dcf-wblwd","ts-price-service","ts-price-service-c4b84c894-dn5pn","ts-rebook-service","ts-rebook-service-776674d89f-j29rc","ts-route-plan-service","ts-route-plan-service-7f4b79f79b-2jclj","ts-route-service","ts-route-service-6db4bdfd5d-zp56g","ts-seat-service","ts-seat-service-5dddf49dfd-zq9bx","ts-security-service","ts-security-service-69797c9fdf-x95mm","ts-station-food-service","ts-station-food-service-6c88c88456-tpjpp","ts-station-service","ts-station-service-75dc8bb94c-vx7l7","ts-ticket-office-service","ts-ticket-office-service-7cd6fff84-vmp45","ts-train-food-service","ts-train-food-service-5cb6b7d98b-qnjbv","ts-train-service","ts-train-service-6ccc6f4465-vjp4c","ts-travel-plan-service","ts-travel-plan-service-56754fc8bc-mpkkg","ts-travel-service","ts-travel-service-5577469b95-rnhtk","ts-travel2-service","ts-travel2-service-859b87cf49-ft2lk","ts-ui-dashboard","ts-ui-dashboard-897fdb6b4-jclw7","ts-user-service","ts-user-service-7fdd6fdfb8-j5bpr","ts-verification-code-service","ts-verification-code-service-5795bcf896-jxc5z","ts-voucher-service","ts-voucher-service-6db9df749b-bzdrc","ts-wait-order-service","ts-wait-order-service-5b9fcd797f-6fgzq","worker1","worker2","worker3","worker4","worker5","worker6"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[3.729,11.186,18.643,26.1,33.557,41.014,48.472,55.929,63.386,70.843,78.3,85.757,93.215,100.672,108.129,115.586,123.043,130.5,137.958,145.415,152.872,160.329,167.786,175.243,182.701,190.158,197.615,205.072,212.529,219.986,227.444,234.901,242.358,249.815,257.272,264.729,272.187,279.644,287.101,294.558,302.015,309.472,316.93,324.387,331.844,339.301,346.758,354.216,361.673,369.13,376.587,384.044,391.501,398.959,406.416,413.873,421.33,428.787,436.244,443.702,451.159,458.616,466.073,473.53]
[M1] rank=1 service=ts-security-service metric=k8s.pod.cpu.node.utilization baseline=0.000382 peak=0.00834 signed_z=30.221 onset_bin=49 onset_rel_s=369.13 persistence_bins=3
values_compact=delta:0.000346,0.000107,0.000099,0,-0.00029,0.000176,0,0,0.000507,0,-0.000366,-0.000366,0.000053,0.000053,-0.000183,0,0.000108,0.000086,0,-0.000065,-0.000066,-0.000039,-0.00004,0.000428,0.000428,-0.000392,-0.000391,0,0.000113,0,0,-0.000082,-0.000034,0,-0.000008,0.000139,0.000139,-0.000098,-0.000098,-0.000031,-0.00003,-0.000073,-0.000073,0.000021,0,0.000016,0.000016,0,-0.000045,0.004138,0.004137,-0.004102,-0.004101,-0.000022,-0.000022,0.000035,0,0.000005,-0.000016,0,0.00004,0.000044,0.000044,-0.000065
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M2] rank=2 service=ts-security-service metric=k8s.pod.cpu.usage baseline=0.048945 peak=1.067548 signed_z=30.221 onset_bin=49 onset_rel_s=369.13 persistence_bins=3
values_compact=delta:0.044299,0.013695,0.012628,0,-0.037095,0.022526,0,0,0.064949,0,-0.04684,-0.046839,0.006772,0.006773,-0.02345,0,0.013837,0.011049,0,-0.008394,-0.008394,-0.005071,-0.00507,0.054774,0.054775,-0.050111,-0.050112,0,0.01447,0,0,-0.010514,-0.004317,0,-0.001088,0.017806,0.017805,-0.012544,-0.012545,-0.003926,-0.003926,-0.009314,-0.009314,0.002648,0,0.002038,0.002037,0,-0.005655,0.529593,0.529593,-0.525024,-0.525025,-0.002825,-0.002824,0.004484,0,0.000697,-0.002041,0,0.005122,0.005622,0.005622,-0.008304
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M3] rank=3 service=ts-security-service metric=k8s.pod.cpu_limit_utilization baseline=0.009789 peak=0.21351 signed_z=30.221 onset_bin=49 onset_rel_s=369.13 persistence_bins=3
values_compact=delta:0.00886,0.002739,0.002525,0,-0.007419,0.004506,0,0,0.012989,0,-0.009368,-0.009367,0.001354,0.001355,-0.00469,0,0.002767,0.00221,0,-0.001679,-0.001679,-0.001014,-0.001014,0.010955,0.010955,-0.010022,-0.010023,0,0.002894,0,0,-0.002103,-0.000863,0,-0.000218,0.003562,0.003561,-0.002509,-0.002509,-0.000785,-0.000786,-0.001862,-0.001863,0.000529,0,0.000408,0.000407,0,-0.001131,0.105919,0.105919,-0.105005,-0.105005,-0.000565,-0.000565,0.000897,0,0.000139,-0.000408,0,0.001024,0.001125,0.001124,-0.001661
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M4] rank=4 service=rabbitmq metric=container.filesystem.available baseline=17145033130.666666 peak=16651554816.0 signed_z=-27.139 onset_bin=38 onset_rel_s=287.101 persistence_bins=2
values_compact=delta:17171779584,-1134592,-10625024,-2117632,-1071104,-1071104,-18878464,-2134016,-1015808,-1015808,39624704,-2232320,-5302272,-5302272,-2183168,-2220032,-5300224,-5300224,7323648,-2260992,-989184,-989184,-2183168,-10641408,-1087488,-1087488,-2371584,-19132416,-1069056,-1069056,7614464,0,39460864,-2416640,-1097728,-1097728,5640192,-2433024,-251529216,-251529216,547876864,-26460160,0,-10964992,-1003520,-129024,-129024,-2121728,-17338368,-180224,-180224,-385024,-344064,20848640,20848640,-323584,-8732672,-278528,-278528,-4790272,-4790272,-1449984,-1585152,-757760
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M5] rank=5 service=ts-admin-route-service metric=container.filesystem.available baseline=17145033130.666666 peak=16651554816.0 signed_z=-27.139 onset_bin=38 onset_rel_s=287.101 persistence_bins=2
values_compact=delta:17171779584,-1134592,-10625024,-2117632,-1071104,-1071104,-18878464,-2134016,-1015808,-1015808,39624704,-2232320,-5302272,-5302272,-2183168,-2220032,-5300224,-5300224,7323648,-2260992,-989184,-989184,-2183168,-10641408,-1087488,-1087488,-2371584,-19132416,-1069056,-1069056,7614464,0,39460864,-2416640,-1097728,-1097728,5640192,-2433024,-251529216,-251529216,547876864,-26460160,0,-10964992,-1003520,-129024,-129024,-2121728,-17338368,-180224,-180224,-385024,-344064,20848640,20848640,-323584,-8732672,-278528,-278528,-4790272,-4790272,-1449984,-1585152,-757760
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M6] rank=6 service=ts-basic-service metric=container.filesystem.available baseline=17145033130.666666 peak=16651554816.0 signed_z=-27.139 onset_bin=38 onset_rel_s=287.101 persistence_bins=2
values_compact=delta:17171779584,-1134592,-10625024,-2117632,-1071104,-1071104,-18878464,-2134016,-1015808,-1015808,39624704,-2232320,-5302272,-5302272,-2183168,-2220032,-5300224,-5300224,7323648,-2260992,-989184,-989184,-2183168,-10641408,-1087488,-1087488,-2371584,-19132416,-1069056,-1069056,7614464,0,39460864,-2416640,-1097728,-1097728,5640192,-2433024,-251529216,-251529216,547876864,-26460160,0,-10964992,-1003520,-129024,-129024,-2121728,-17338368,-180224,-180224,-385024,-344064,20848640,20848640,-323584,-8732672,-278528,-278528,-4790272,-4790272,-1449984,-1585152,-757760
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M7] rank=7 service=ts-config-service metric=container.filesystem.available baseline=17145033130.666666 peak=16651554816.0 signed_z=-27.139 onset_bin=38 onset_rel_s=287.101 persistence_bins=2
values_compact=delta:17171779584,-1134592,-10625024,-2117632,-1071104,-1071104,-18878464,-2134016,-1015808,-1015808,39624704,-2232320,-5302272,-5302272,-2183168,-2220032,-5300224,-5300224,7323648,-2260992,-989184,-989184,-2183168,-10641408,-1087488,-1087488,-2371584,-19132416,-1069056,-1069056,7614464,0,39460864,-2416640,-1097728,-1097728,5640192,-2433024,-251529216,-251529216,547876864,-26460160,0,-10964992,-1003520,-129024,-129024,-2121728,-17338368,-180224,-180224,-385024,-344064,20848640,20848640,-323584,-8732672,-278528,-278528,-4790272,-4790272,-1449984,-1585152,-757760
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M8] rank=8 service=ts-consign-service metric=container.filesystem.available baseline=17145033130.666666 peak=16651554816.0 signed_z=-27.139 onset_bin=38 onset_rel_s=287.101 persistence_bins=2
values_compact=delta:17171779584,-1134592,-10625024,-2117632,-1071104,-1071104,-18878464,-2134016,-1015808,-1015808,39624704,-2232320,-5302272,-5302272,-2183168,-2220032,-5300224,-5300224,7323648,-2260992,-989184,-989184,-2183168,-10641408,-1087488,-1087488,-2371584,-19132416,-1069056,-1069056,7614464,0,39460864,-2416640,-1097728,-1097728,5640192,-2433024,-251529216,-251529216,547876864,-26460160,0,-10964992,-1003520,-129024,-129024,-2121728,-17338368,-180224,-180224,-385024,-344064,20848640,20848640,-323584,-8732672,-278528,-278528,-4790272,-4790272,-1449984,-1585152,-757760
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M9] rank=9 service=ts-execute-service metric=container.filesystem.available baseline=17145033130.666666 peak=16651554816.0 signed_z=-27.139 onset_bin=38 onset_rel_s=287.101 persistence_bins=2
values_compact=delta:17171779584,-1134592,-10625024,-2117632,-1071104,-1071104,-18878464,-2134016,-1015808,-1015808,39624704,-2232320,-5302272,-5302272,-2183168,-2220032,-5300224,-5300224,7323648,-2260992,-989184,-989184,-2183168,-10641408,-1087488,-1087488,-2371584,-19132416,-1069056,-1069056,7614464,0,39460864,-2416640,-1097728,-1097728,5640192,-2433024,-251529216,-251529216,547876864,-26460160,0,-10964992,-1003520,-129024,-129024,-2121728,-17338368,-180224,-180224,-385024,-344064,20848640,20848640,-323584,-8732672,-278528,-278528,-4790272,-4790272,-1449984,-1585152,-757760
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M10] rank=10 service=ts-ticket-office-service metric=container.filesystem.available baseline=17145033130.666666 peak=16651554816.0 signed_z=-27.139 onset_bin=38 onset_rel_s=287.101 persistence_bins=2
values_compact=delta:17171779584,-1134592,-10625024,-2117632,-1071104,-1071104,-18878464,-2134016,-1015808,-1015808,39624704,-2232320,-5302272,-5302272,-2183168,-2220032,-5300224,-5300224,7323648,-2260992,-989184,-989184,-2183168,-10641408,-1087488,-1087488,-2371584,-19132416,-1069056,-1069056,7614464,0,39460864,-2416640,-1097728,-1097728,5640192,-2433024,-251529216,-251529216,547876864,-26460160,0,-10964992,-1003520,-129024,-129024,-2121728,-17338368,-180224,-180224,-385024,-344064,20848640,20848640,-323584,-8732672,-278528,-278528,-4790272,-4790272,-1449984,-1585152,-757760
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M11] rank=11 service=ts-preserve-service metric=container.memory.rss baseline=710946560.0 peak=749084672.0 signed_z=27.102 onset_bin=33 onset_rel_s=249.815 persistence_bins=31
values_compact=delta:710262784,2056192,0,-4239360,0,1044480,0,0,217088,0,0,188416,0,2367488,0,69632,0,843776,0,-1085440,0,77824,0,49152,0,696320,0,-1099776,-1099776,258048,258048,200704,200704,37818368,0,-26841088,204800,0,0,5419008,4096,0,0,0,0,-65536,0,0,0,2314240,0,24576,24576,0,102400,0,45056,32768,32768,12288,12288,1554432,1554432,4820992
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M12] rank=12 service=rabbitmq metric=k8s.pod.filesystem.available baseline=17144874496.0 peak=16651554816.0 signed_z=-26.72 onset_bin=38 onset_rel_s=287.101 persistence_bins=2
values_compact=delta:17171779584,-1134592,-10625024,-2117632,-1071104,-1071104,-18878464,-2134016,-1015808,-1015808,39624704,-2232320,-5302272,-5302272,-2183168,-2220032,-5300224,-5300224,7323648,-2260992,-989184,-989184,-2183168,-10641408,-1087488,-1087488,-2371584,-19132416,-1069056,-1069056,3807232,3807232,39460864,-2416640,-1097728,-1097728,5640192,-2433024,-251529216,-251529216,547876864,-26460160,0,-10964992,-1003520,-129024,-129024,-2121728,-17338368,-180224,-180224,-385024,-344064,20848640,20848640,-323584,-8732672,0,-557056,-4790272,-4790272,-1449984,-1585152,-757760
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[366.8977360725403,386.7991156578064]

=== LOG SUMMARY ===
{"entries":[{"error_logs":5950,"error_pct":19.25,"service":"ts-seat-service","total_logs":30905},{"error_logs":578,"error_pct":16.16,"service":"ts-food-service","total_logs":3577},{"error_logs":233,"error_pct":6.1,"service":"ts-preserve-service","total_logs":3818},{"error_logs":227,"error_pct":2.03,"service":"ts-order-service","total_logs":11196},{"error_logs":192,"error_pct":40.0,"service":"ts-delivery-service","total_logs":480},{"error_logs":190,"error_pct":40.0,"service":"ts-notification-service","total_logs":475},{"error_logs":14,"error_pct":0.1,"service":"ts-ui-dashboard","total_logs":13342},{"error_logs":11,"error_pct":0.07,"service":"ts-travel-service","total_logs":14984}],"mode":"errors","omitted_services":23,"service_count":31}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":1785.3,"error_pct":0.0,"p95_during_ms":393.83372019999223,"p95_pre_ms":20.889183400000004,"service":"ts-security-service","spans":2910},{"delta_pct":344.3,"error_pct":0.0,"p95_during_ms":1600.261926599996,"p95_pre_ms":360.20847125,"service":"ts-preserve-service","spans":2491},{"delta_pct":307.9,"error_pct":1.03,"p95_during_ms":162.2052626,"p95_pre_ms":39.76871339999998,"service":"ts-basic-service","spans":12642},{"delta_pct":195.7,"error_pct":0.0,"p95_during_ms":243.32219479999998,"p95_pre_ms":82.29403949999995,"service":"ts-travel2-service","spans":9717},{"delta_pct":128.0,"error_pct":0.9,"p95_during_ms":239.18113899999997,"p95_pre_ms":104.89626814999995,"service":"ts-travel-service","spans":16255},{"delta_pct":106.9,"error_pct":5.26,"p95_during_ms":974.1277737999927,"p95_pre_ms":470.87019654999995,"service":"ts-route-plan-service","spans":3119},{"delta_pct":82.2,"error_pct":0.26,"p95_during_ms":294.3551201999997,"p95_pre_ms":161.56502639999994,"service":"loadgenerator","spans":13342},{"delta_pct":81.5,"error_pct":0.26,"p95_during_ms":290.3775350499997,"p95_pre_ms":159.95057079999995,"service":"ts-ui-dashboard","spans":13342}],"omitted_services":22,"service_count":30}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=35 omitted_edges=0
[{"evidence_source":"metric","onset_rel_s":247.2,"rank":1,"service":"ts-preserve-service","severity_z":27.102},{"evidence_source":"metric","onset_rel_s":290.4,"rank":2,"service":"rabbitmq","severity_z":27.139},{"evidence_source":"metric","onset_rel_s":290.4,"rank":3,"service":"ts-admin-route-service","severity_z":27.139},{"evidence_source":"metric","onset_rel_s":290.4,"rank":4,"service":"ts-basic-service","severity_z":27.139},{"evidence_source":"metric","onset_rel_s":290.4,"rank":5,"service":"ts-config-service","severity_z":27.139},{"evidence_source":"metric","onset_rel_s":290.4,"rank":6,"service":"ts-execute-service","severity_z":27.139},{"evidence_source":"metric","onset_rel_s":290.4,"rank":7,"service":"ts-ticket-office-service","severity_z":27.139},{"evidence_source":"metric","onset_rel_s":331.8,"rank":8,"service":"ts-train-food-service","severity_z":19.51},{"evidence_source":"metric","onset_rel_s":332.4,"rank":9,"service":"ts-wait-order-service","severity_z":14.277},{"evidence_source":"metric","onset_rel_s":355.2,"rank":10,"service":"ts-voucher-service","severity_z":24.386},{"evidence_source":"metric","onset_rel_s":361.2,"rank":11,"service":"loadgenerator","severity_z":17.401},{"evidence_source":"trace","onset_rel_s":372.6,"rank":12,"service":"ts-security-service","severity_z":8.538},{"evidence_source":"trace","onset_rel_s":442.2,"rank":13,"service":"ts-station-food-service","severity_z":97.546},{"evidence_source":"trace","onset_rel_s":462.6,"rank":14,"service":"ts-consign-service","severity_z":66.57}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"ts-basic-service","caller":"ts-preserve-service"},{"callee":"ts-security-service","caller":"ts-preserve-service"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

[excluded before optimizer]

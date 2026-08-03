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
opaque_id: INC-98C49B188816
observation_window={"duration_rel_s":479.719,"source_metric_rows":952}
selection_summary={"candidate_count":104,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":899,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["loadgenerator","loadgenerator-54767f9c44-94km2","mysql","mysql-0","rabbitmq","rabbitmq-0","ts-admin-basic-info-service","ts-admin-basic-info-service-b64c7b7-h2vkd","ts-admin-order-service","ts-admin-order-service-f7bf478bb-xt4zz","ts-admin-route-service","ts-admin-route-service-85856d6455-kvwtz","ts-admin-travel-service","ts-admin-travel-service-5b6689466b-6ksxr","ts-admin-user-service","ts-admin-user-service-8c75655c-8cwdx","ts-assurance-service","ts-assurance-service-657d8b7f65-s7khp","ts-auth-service","ts-auth-service-57c4c888c4-6qtxl","ts-avatar-service","ts-avatar-service-8579dbd4cd-tzxg8","ts-basic-service","ts-basic-service-76c5ccfcd6-fgmmh","ts-cancel-service","ts-cancel-service-7d9cbb9cd-nt44z","ts-config-service","ts-config-service-78f6dc4b98-7gb7d","ts-consign-price-service","ts-consign-price-service-6f946d8b6f-v4xt4","ts-consign-service","ts-consign-service-5495cf9f77-rbc5d","ts-contacts-service","ts-contacts-service-85bdbb4db9-5bkvs","ts-delivery-service","ts-delivery-service-9f4d744d4-zpknw","ts-execute-service","ts-execute-service-f6d766c7f-rzbpc","ts-food-delivery-service","ts-food-delivery-service-84cd4ff859-kg82k","ts-food-service","ts-food-service-767cc8b664-gb5gd","ts-gateway-service","ts-gateway-service-745c4c9766-6lqv8","ts-inside-payment-service","ts-inside-payment-service-845d7548ff-hbdqx","ts-news-service","ts-news-service-b7d748896-xxdmh","ts-notification-service","ts-notification-service-f4ff74847-pxvkn","ts-order-other-service","ts-order-other-service-5dc8c449f5-lttt4","ts-order-service","ts-order-service-85bcb6c549-skm8k","ts-payment-service","ts-payment-service-b6fb8dd98-pk6mv","ts-preserve-other-service","ts-preserve-other-service-67f7b68c9f-48smw","ts-preserve-service","ts-preserve-service-78dddfd844-l68jr","ts-price-service","ts-price-service-5b5cf4f8f7-69zq7","ts-rebook-service","ts-rebook-service-5cccb444bd-txvsr","ts-route-plan-service","ts-route-plan-service-74477cfd99-85hrd","ts-route-service","ts-route-service-7cc65f5db5-hbbkg","ts-seat-service","ts-seat-service-5c5db97cb9-587vl","ts-security-service","ts-security-service-69bd8966cd-6r2nr","ts-station-food-service","ts-station-food-service-7d5fbbf595-vl5qr","ts-station-service","ts-station-service-6d944cc5b-pxn58","ts-ticket-office-service","ts-ticket-office-service-555bbf544c-mw6q6","ts-train-food-service","ts-train-food-service-6d4fffffc-8vqmw","ts-train-service","ts-train-service-67cdc58c6b-8n9xk","ts-travel-plan-service","ts-travel-plan-service-668ddf994d-wd8st","ts-travel-service","ts-travel-service-6dbb78b4cb-fjvmv","ts-travel2-service","ts-travel2-service-59f6556598-vfdwd","ts-ui-dashboard","ts-ui-dashboard-569d6d999-g96bw","ts-user-service","ts-user-service-5c8779495f-gwbzs","ts-verification-code-service","ts-verification-code-service-d8f8f67ff-stbzr","ts-voucher-service","ts-voucher-service-d969f6d9f-jjdvx","ts-wait-order-service","ts-wait-order-service-77f7547fb8-x6wxc","worker1","worker2","worker3","worker4","worker5","worker6"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[3.748,11.243,18.739,26.235,33.73,41.226,48.721,56.217,63.713,71.208,78.704,86.2,93.695,101.191,108.686,116.182,123.678,131.173,138.669,146.164,153.66,161.156,168.651,176.147,183.643,191.138,198.634,206.129,213.625,221.121,228.616,236.112,243.607,251.103,258.599,266.094,273.59,281.085,288.581,296.077,303.572,311.068,318.564,326.059,333.555,341.05,348.546,356.042,363.537,371.033,378.528,386.024,393.52,401.015,408.511,416.006,423.502,430.998,438.493,445.989,453.485,460.98,468.476,475.971]
[M1] rank=1 service=ts-admin-user-service metric=k8s.pod.cpu.node.utilization baseline=4.1e-05 peak=0.006525 signed_z=777.177 onset_bin=54 onset_rel_s=408.511 persistence_bins=4
values_compact=delta:0.000043,0.000003,-0.000007,-0.000007,0,-0.000003,0.000006,0.000005,-0.000008,0,0.000001,0,0,0.000001,0,0.000008,0,-0.000002,0,-0.000004,0,0,0.000006,0,0.000015,0,-0.000005,0,-0.000005,0.000006,0,0.000004,-0.000004,-0.000004,0,-0.000001,-0.000005,-0.000004,0.000017,0,-0.000011,0,0.000004,0,-0.000005,-0.000005,0.000002,0.000002,-0.000001,0,0.000002,0.000001,-0.000003,0,0.001597,0,0.004886,0,-0.006468,-0.000004,-0.000005,-0.000001,-0.000002,0
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,1,2,1,2,1,2,1,2
[M2] rank=2 service=ts-admin-user-service metric=k8s.pod.cpu.usage baseline=0.005225 peak=0.835142 signed_z=777.177 onset_bin=54 onset_rel_s=408.511 persistence_bins=4
values_compact=delta:0.00551,0.000442,-0.000925,-0.000924,0,-0.000339,0.000663,0.000663,-0.000971,0,0.000064,0.000065,0.000031,0.000031,0,0.001023,0,-0.000231,0,-0.000438,0,0,0.000662,0,0.00193,0,-0.000556,0,-0.00073,0.00079,0,0.000522,-0.000487,-0.000487,0,-0.00022,-0.000522,-0.000523,0.002079,0,-0.00142,0,0.000594,0,-0.000637,-0.000638,0.000248,0.000247,-0.000077,-0.000076,0.000224,0.000225,-0.000397,0,0.20441,0,0.625317,0,-0.827829,-0.000562,-0.000563,-0.000205,-0.000206,0
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,1,2,1,2,1,2,1,2
[M3] rank=3 service=ts-admin-user-service metric=k8s.pod.cpu_limit_utilization baseline=0.001045 peak=0.167028 signed_z=777.177 onset_bin=54 onset_rel_s=408.511 persistence_bins=4
values_compact=delta:0.001102,0.000088,-0.000185,-0.000184,0,-0.000068,0.000132,0.000133,-0.000194,0,0.000013,0.000013,0.000006,0.000006,0,0.000205,0,-0.000047,0,-0.000087,0,0,0.000132,0,0.000386,0,-0.000111,0,-0.000146,0.000158,0,0.000104,-0.000097,-0.000097,0,-0.000044,-0.000105,-0.000104,0.000415,0,-0.000284,0,0.000119,0,-0.000127,-0.000128,0.00005,0.000049,-0.000015,-0.000015,0.000044,0.000045,-0.000079,0,0.040882,0,0.125063,0,-0.165565,-0.000113,-0.000112,-0.000041,-0.000042,0
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,1,2,1,2,1,2,1,2
[M4] rank=4 service=ts-admin-user-service metric=container.cpu.usage baseline=0.005289 peak=0.858595 signed_z=699.256 onset_bin=55 onset_rel_s=416.006 persistence_bins=3
values_compact=delta:0.005567,-0.000564,-0.000909,0,-0.000221,0,0.000102,0,0.000902,0,-0.000503,0,-0.000317,0.000193,0,0.00137,0,-0.000311,0,0,-0.000626,0.000539,0,0.00269,0,-0.001705,0,0.000185,-0.000262,-0.000263,0.001904,0,-0.000642,-0.000642,-0.000121,-0.00012,-0.000465,-0.000464,0.000477,0.000478,-0.000235,-0.000235,0,0.00027,-0.000525,-0.000525,0.000236,0.000236,0.000213,0.000212,-0.000424,-0.000425,0,0.000774,0,0.426375,0.426376,-0.425885,-0.425885,-0.00054,0,0.000067,0.000067,0.000104
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,1,2,1,2,1,2,1,2
[M5] rank=5 service=ts-delivery-service metric=k8s.pod.cpu.node.utilization baseline=6.9e-05 peak=0.002122 signed_z=92.246 onset_bin=40 onset_rel_s=303.572 persistence_bins=3
values_compact=delta:0.000101,0,0.000029,0,-0.000072,-0.000007,0,0.000009,0,-0.000011,0,0,-0.000005,0.000007,0,0.000012,0,-0.000007,0,0.000009,-0.000002,-0.000002,0,0.000027,0,0.000009,-0.000016,-0.000015,0,0.000001,0.000009,0.000009,-0.000011,0.000016,0,-0.000022,-0.000008,-0.000008,0.000003,0.000004,0.001031,0.001032,-0.001027,-0.001028,-0.000002,-0.000003,0,0.000014,0,-0.000007,0.000004,0.000005,0,0,0,0.000045,0,0,-0.000036,0,0,0.000011,0,-0.000013
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,1,2,1,2
[M6] rank=6 service=ts-delivery-service metric=k8s.pod.cpu.usage baseline=0.008895 peak=0.271654 signed_z=92.246 onset_bin=40 onset_rel_s=303.572 persistence_bins=3
values_compact=delta:0.012989,0,0.003662,0,-0.009178,-0.000998,0,0.001223,0,-0.001444,0,0,-0.000575,0.000791,0,0.001623,0,-0.000984,0,0.001216,-0.000239,-0.000239,0,0.00337,0,0.001195,-0.001998,-0.001999,0.000065,0.000066,0.001177,0.001177,-0.001448,0.002076,0,-0.002858,-0.000998,-0.000997,0.000411,0.00041,0.132079,0.132079,-0.131522,-0.131522,-0.00035,-0.00035,0,0.001868,0,-0.000952,0.00055,0.00055,0,0.000074,0,0.005702,0,0,-0.004512,0,0,0.001401,0,-0.001696
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,1,2,1,2
[M7] rank=7 service=ts-delivery-service metric=k8s.pod.cpu_limit_utilization baseline=0.001779 peak=0.054331 signed_z=92.246 onset_bin=40 onset_rel_s=303.572 persistence_bins=3
values_compact=delta:0.002598,0,0.000732,0,-0.001835,-0.0002,0,0.000245,0,-0.000289,0,0,-0.000115,0.000158,0,0.000325,0,-0.000197,0,0.000243,-0.000048,-0.000048,0,0.000674,0,0.000239,-0.000399,-0.0004,0.000013,0.000013,0.000236,0.000235,-0.00029,0.000416,0,-0.000572,-0.0002,-0.000199,0.000082,0.000082,0.026416,0.026416,-0.026305,-0.026304,-0.00007,-0.00007,0,0.000374,0,-0.000191,0.00011,0.00011,0,0.000015,0,0.00114,0,0,-0.000902,0,0,0.00028,0,-0.000339
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,1,2,1,2
[M8] rank=8 service=ts-delivery-service metric=container.cpu.usage baseline=0.008606 peak=0.255432 signed_z=82.695 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.013382,0.004662,-0.004371,-0.004371,-0.002886,0,0.000227,0.000226,0.000231,0.00023,-0.001657,0,-0.00017,0,0.001567,0,0.000383,0.000384,-0.000099,-0.000098,-0.000661,0,0.002045,0.002045,-0.000032,-0.000032,-0.000279,-0.000279,-0.002212,0,0.00189,0,0.000225,0.000225,0,-0.000982,0,0,-0.003034,0,0.248873,-0.247264,0,0,0.000202,0.002069,0,0,-0.002222,0.001119,0,0,0.000516,-0.000194,0,0.007229,0,-0.005093,0,0.001378,0,-0.001337,-0.001337,0.000514
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,1,2,1,2
[M9] rank=9 service=ts-admin-user-service metric=k8s.pod.memory.rss baseline=641048576.0 peak=645480448.0 signed_z=46.663 onset_bin=54 onset_rel_s=408.511 persistence_bins=10
values_compact=delta:641132544,124928,-174080,-174080,0,0,36864,36864,0,0,0,0,2048,2048,0,147456,0,16384,0,0,0,0,0,0,-118784,0,0,0,0,0,0,0,0,0,0,118784,0,0,12288,0,0,0,-65536,0,-34816,-34816,6144,6144,0,0,8192,8192,0,0,2297856,0,2125824,0,0,0,0,0,0,0
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,1,2,1,2,1,2,1,2
[M10] rank=10 service=ts-admin-user-service metric=container.memory.rss baseline=641012480.0 peak=645435392.0 signed_z=45.513 onset_bin=55 onset_rel_s=416.006 persistence_bins=9
values_compact=delta:641193984,18432,-69632,0,-278528,0,0,0,73728,0,0,0,0,4096,0,147456,0,16384,0,0,0,0,0,-118784,0,0,0,0,0,0,0,0,0,0,59392,59392,0,0,6144,6144,0,0,0,-135168,0,0,6144,6144,8192,8192,0,0,0,0,0,2211840,2211840,0,0,0,0,0,0,-32768
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,1,2,1,2,1,2,1,2
[M11] rank=11 service=ts-route-plan-service metric=k8s.pod.filesystem.usage baseline=533930.666667 peak=1359872.0 signed_z=33.482 onset_bin=33 onset_rel_s=251.103 persistence_bins=31
values_compact=delta:487424,0,4096,6144,2048,4096,4096,4096,4096,2048,2048,4096,4096,2048,2048,4096,4096,2048,2048,2048,2048,4096,0,2048,2048,0,4096,0,0,2048,2048,2048,2048,65536,16384,32768,65536,30720,14336,20480,45056,45056,53248,12288,40960,28672,24576,47104,67584,22528,22528,28672,8192,0,16384,2048,18432,12288,0,0,4096,16384,0,28672
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,2,1,2
[M12] rank=12 service=ts-admin-user-service metric=k8s.pod.memory.node.utilization baseline=0.004832 peak=0.004864 signed_z=32.551 onset_bin=54 onset_rel_s=408.511 persistence_bins=10
values_compact=rle:0.004833*1,0.004834*1,0.004832*1,0.00483*3,0.004831*6,0.004832*1,0.004833*2,0.004832*2,0.004833*7,0.004831*11,0.004832*7,0.004831*12,0.004848*2,0.004864*8
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,1,2,1,2,1,2,1,2

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[418.10392570495605,437.88822960853577]

=== LOG SUMMARY ===
{"entries":[{"error_logs":1341,"error_pct":19.38,"service":"ts-seat-service","total_logs":6921},{"error_logs":186,"error_pct":18.4,"service":"ts-food-service","total_logs":1011},{"error_logs":96,"error_pct":25.0,"service":"ts-notification-service","total_logs":384},{"error_logs":96,"error_pct":25.0,"service":"ts-delivery-service","total_logs":384},{"error_logs":85,"error_pct":2.13,"service":"ts-ui-dashboard","total_logs":3984},{"error_logs":83,"error_pct":2.43,"service":"ts-travel-service","total_logs":3416},{"error_logs":48,"error_pct":6.69,"service":"ts-route-plan-service","total_logs":718},{"error_logs":48,"error_pct":7.35,"service":"ts-travel-plan-service","total_logs":653}],"mode":"errors","omitted_services":22,"service_count":30}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":2252.1,"error_pct":0.0,"p95_during_ms":201.4048746,"p95_pre_ms":8.5628008,"service":"ts-user-service","spans":3510},{"delta_pct":1858.2,"error_pct":0.0,"p95_during_ms":127.296453,"p95_pre_ms":6.500659099999987,"service":"ts-config-service","spans":6705},{"delta_pct":800.3,"error_pct":0.0,"p95_during_ms":114.15317425,"p95_pre_ms":12.67926125,"service":"ts-route-service","spans":18422},{"delta_pct":549.3,"error_pct":0.0,"p95_during_ms":88.67795925,"p95_pre_ms":13.656902349999996,"service":"ts-contacts-service","spans":1294},{"delta_pct":499.5,"error_pct":0.0,"p95_during_ms":64.39921219999998,"p95_pre_ms":10.74231364999997,"service":"ts-order-service","spans":7145},{"delta_pct":456.4,"error_pct":0.0,"p95_during_ms":87.2240591,"p95_pre_ms":15.676004599999999,"service":"ts-train-food-service","spans":1033},{"delta_pct":345.5,"error_pct":0.0,"p95_during_ms":147.69801539999995,"p95_pre_ms":33.15593859999997,"service":"ts-seat-service","spans":5526},{"delta_pct":343.7,"error_pct":0.0,"p95_during_ms":31.076672249999987,"p95_pre_ms":7.003975200000004,"service":"ts-train-service","spans":4949}],"omitted_services":21,"service_count":29}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=35 omitted_edges=0
[{"evidence_source":"metric","onset_rel_s":286.8,"rank":1,"service":"mysql","severity_z":17.458},{"evidence_source":"metric","onset_rel_s":286.8,"rank":2,"service":"rabbitmq","severity_z":17.458},{"evidence_source":"metric","onset_rel_s":286.8,"rank":3,"service":"ts-admin-basic-info-service","severity_z":17.458},{"evidence_source":"metric","onset_rel_s":286.8,"rank":4,"service":"ts-consign-price-service","severity_z":17.458},{"evidence_source":"metric","onset_rel_s":286.8,"rank":5,"service":"ts-seat-service","severity_z":17.458},{"evidence_source":"metric","onset_rel_s":306.0,"rank":6,"service":"ts-delivery-service","severity_z":92.246},{"evidence_source":"metric","onset_rel_s":316.8,"rank":7,"service":"ts-travel-plan-service","severity_z":20.374},{"evidence_source":"metric","onset_rel_s":318.0,"rank":8,"service":"ts-route-plan-service","severity_z":33.482},{"evidence_source":"metric","onset_rel_s":422.4,"rank":9,"service":"ts-admin-user-service","severity_z":777.177},{"evidence_source":"trace","onset_rel_s":424.8,"rank":10,"service":"ts-verification-code-service","severity_z":999.0},{"evidence_source":"trace","onset_rel_s":424.8,"rank":11,"service":"ts-train-service","severity_z":10.69},{"evidence_source":"metric","onset_rel_s":433.8,"rank":12,"service":"ts-order-other-service","severity_z":17.34},{"evidence_source":"trace","onset_rel_s":444.6,"rank":13,"service":"loadgenerator","severity_z":7.066},{"evidence_source":"metric","onset_rel_s":467.4,"rank":14,"service":"ts-news-service","severity_z":15.583}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"ts-order-other-service","caller":"ts-seat-service"},{"callee":"ts-route-plan-service","caller":"ts-travel-plan-service"},{"callee":"ts-seat-service","caller":"ts-travel-plan-service"},{"callee":"ts-train-service","caller":"ts-travel-plan-service"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

[excluded before optimizer]

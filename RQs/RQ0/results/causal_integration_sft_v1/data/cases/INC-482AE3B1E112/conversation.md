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
opaque_id: INC-482AE3B1E112
observation_window={"duration_rel_s":479.292,"source_metric_rows":952}
selection_summary={"candidate_count":104,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":901,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["loadgenerator","loadgenerator-76c5949c78-2f2v8","mysql","mysql-0","rabbitmq","rabbitmq-0","ts-admin-basic-info-service","ts-admin-basic-info-service-579bc4cd8d-tqnhj","ts-admin-order-service","ts-admin-order-service-76fc4c68d5-vsq8b","ts-admin-route-service","ts-admin-route-service-85bffd5f6-wz6lg","ts-admin-travel-service","ts-admin-travel-service-797ccbcff7-hm6v6","ts-admin-user-service","ts-admin-user-service-7874ccc7c4-xwn2b","ts-assurance-service","ts-assurance-service-d87bf675d-7hsxm","ts-auth-service","ts-auth-service-6477f4967c-rf7hx","ts-avatar-service","ts-avatar-service-74fd5ff4c7-7sjms","ts-basic-service","ts-basic-service-59f887c7d5-5f9zz","ts-cancel-service","ts-cancel-service-67454d8789-zscnv","ts-config-service","ts-config-service-56457f8db5-9ddxx","ts-consign-price-service","ts-consign-price-service-54b69c6854-2hmp7","ts-consign-service","ts-consign-service-686f9c998-9hg9c","ts-contacts-service","ts-contacts-service-7df9fc84b6-76nst","ts-delivery-service","ts-delivery-service-55b55bb555-xxmx5","ts-execute-service","ts-execute-service-64b744d564-7hjc6","ts-food-delivery-service","ts-food-delivery-service-599dfbdb6d-84zgr","ts-food-service","ts-food-service-755696bb9f-zsnd8","ts-gateway-service","ts-gateway-service-9cdfbbdfc-fp9ds","ts-inside-payment-service","ts-inside-payment-service-7666f6c64d-kdgzt","ts-news-service","ts-news-service-7869d45c45-rrwwf","ts-notification-service","ts-notification-service-b5b74bb44-x5442","ts-order-other-service","ts-order-other-service-67cbddcb88-8pds6","ts-order-service","ts-order-service-85b9979d59-8jkcz","ts-payment-service","ts-payment-service-5df5775665-psmr8","ts-preserve-other-service","ts-preserve-other-service-74f69f9db4-5c84z","ts-preserve-service","ts-preserve-service-7f8d678dcf-d4gmd","ts-price-service","ts-price-service-c4b84c894-964zp","ts-rebook-service","ts-rebook-service-776674d89f-qfqv9","ts-route-plan-service","ts-route-plan-service-7f4b79f79b-2ppzs","ts-route-service","ts-route-service-6db4bdfd5d-67sft","ts-seat-service","ts-seat-service-5dddf49dfd-f4phw","ts-security-service","ts-security-service-69797c9fdf-d8njk","ts-station-food-service","ts-station-food-service-6c88c88456-4w6h9","ts-station-service","ts-station-service-75dc8bb94c-2rz8w","ts-ticket-office-service","ts-ticket-office-service-7cd6fff84-gvqfw","ts-train-food-service","ts-train-food-service-5cb6b7d98b-zzgp9","ts-train-service","ts-train-service-6ccc6f4465-kq58l","ts-travel-plan-service","ts-travel-plan-service-56754fc8bc-nxd65","ts-travel-service","ts-travel-service-5577469b95-vkvn9","ts-travel2-service","ts-travel2-service-859b87cf49-xftds","ts-ui-dashboard","ts-ui-dashboard-897fdb6b4-hvsx7","ts-user-service","ts-user-service-7fdd6fdfb8-6h47d","ts-verification-code-service","ts-verification-code-service-5795bcf896-s2zpz","ts-voucher-service","ts-voucher-service-6db9df749b-jsw62","ts-wait-order-service","ts-wait-order-service-5b9fcd797f-v66n8","worker1","worker2","worker3","worker4","worker5","worker6"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[3.744,11.233,18.722,26.211,33.7,41.189,48.678,56.167,63.656,71.145,78.634,86.123,93.612,101.101,108.589,116.078,123.567,131.056,138.545,146.034,153.523,161.012,168.501,175.99,183.479,190.968,198.457,205.946,213.435,220.923,228.412,235.901,243.39,250.879,258.368,265.857,273.346,280.835,288.324,295.813,303.302,310.791,318.28,325.768,333.257,340.746,348.235,355.724,363.213,370.702,378.191,385.68,393.169,400.658,408.147,415.636,423.125,430.614,438.102,445.591,453.08,460.569,468.058,475.547]
[M1] rank=1 service=rabbitmq metric=container.memory.rss baseline=152635136.0 peak=152772608.0 signed_z=67.656 onset_bin=34 onset_rel_s=258.368 persistence_bins=30
values_compact=rle:152633344*18,152637440*16,152641536*2,152649728*1,152670208*1,152690688*3,152692736*1,152694784*16,152772608*1,152694784*5
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,1,2,1,2,1,2,1,2,2
[M2] rank=2 service=ts-news-service metric=k8s.pod.memory.usage baseline=9594709.333333 peak=10915840.0 signed_z=53.665 onset_bin=42 onset_rel_s=318.28 persistence_bins=2
values_compact=rle:9560064*11,9613312*18,9605120*13,10915840*2,9609216*15,9607168*1,9605120*4
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M3] rank=3 service=ts-news-service metric=k8s.pod.memory.working_set baseline=9594709.333333 peak=10915840.0 signed_z=53.665 onset_bin=42 onset_rel_s=318.28 persistence_bins=2
values_compact=rle:9560064*11,9613312*18,9605120*13,10915840*2,9609216*15,9607168*1,9605120*4
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M4] rank=4 service=ts-news-service metric=k8s.pod.memory_limit_utilization baseline=0.002979 peak=0.003389 signed_z=53.665 onset_bin=42 onset_rel_s=318.28 persistence_bins=2
values_compact=rle:0.002968*11,0.002984*18,0.002982*13,0.003389*2,0.002983*15,0.002982*5
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M5] rank=5 service=ts-news-service metric=k8s.pod.memory.node.utilization baseline=7.1e-05 peak=8.1e-05 signed_z=53.665 onset_bin=42 onset_rel_s=318.28 persistence_bins=2
values_compact=rle:0.000071*42,0.000081*2,0.000071*20
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M6] rank=6 service=ts-news-service metric=k8s.pod.memory.available baseline=3211630762.666667 peak=3210309632.0 signed_z=-53.665 onset_bin=42 onset_rel_s=318.28 persistence_bins=2
values_compact=rle:3211665408*11,3211612160*18,3211620352*13,3210309632*2,3211616256*15,3211618304*1,3211620352*4
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M7] rank=7 service=rabbitmq metric=k8s.pod.memory.rss baseline=152672085.333333 peak=152731648.0 signed_z=29.185 onset_bin=35 onset_rel_s=265.857 persistence_bins=29
values_compact=rle:152670208*17,152672256*1,152674304*17,152678400*2,152727552*4,152729600*1,152731648*22
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,1,2,1,2,1,2,1,2,2
[M8] rank=8 service=ts-preserve-service metric=k8s.pod.cpu.node.utilization baseline=0.00038 peak=0.007214 signed_z=26.071 onset_bin=33 onset_rel_s=250.879 persistence_bins=3
values_compact=delta:0.00038,0,0.000374,0,0,-0.000433,-0.000052,0,0.000555,0,-0.000533,-0.000062,-0.000062,0,0.000633,-0.0003,-0.0003,0.00002,0,0.00014,0,0.000261,0.000261,-0.000318,-0.000317,-0.000009,-0.000008,-0.00005,-0.000051,-0.000026,-0.000027,0.000022,0,0.007116,0,-0.003588,-0.003588,0.000005,0.000005,0,-0.000009,0,-0.000005,0,0.00003,0,0,-0.000016,0,0.000004,0.000005,-0.000016,0,0.000037,0.000038,-0.000039,0,0.000026,0.000026,-0.000024,-0.000024,-0.000016,0,0.00001
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M9] rank=9 service=ts-preserve-service metric=k8s.pod.cpu.usage baseline=0.048629 peak=0.923379 signed_z=26.071 onset_bin=33 onset_rel_s=250.879 persistence_bins=3
values_compact=delta:0.048665,0,0.047864,0,0,-0.05538,-0.006741,0,0.071064,0,-0.068279,-0.007926,-0.007927,0,0.081015,-0.038406,-0.038406,0.002677,0,0.017816,0,0.033432,0.033431,-0.040664,-0.040665,-0.001074,-0.001074,-0.006443,-0.006444,-0.003413,-0.003412,0.002848,0,0.910821,0,-0.459257,-0.459257,0.000629,0.000628,0,-0.001088,0,-0.00069,0,0.00388,0,0,-0.002019,0,0.000514,0.000514,-0.002029,0,0.004808,0.004808,-0.00491,0,0.003311,0.00331,-0.003061,-0.003061,-0.002035,0,0.001176
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M10] rank=10 service=ts-preserve-service metric=k8s.pod.cpu_limit_utilization baseline=0.009726 peak=0.184676 signed_z=26.071 onset_bin=33 onset_rel_s=250.879 persistence_bins=3
values_compact=delta:0.009733,0,0.009573,0,0,-0.011076,-0.001348,0,0.014212,0,-0.013655,-0.001586,-0.001585,0,0.016203,-0.007681,-0.007681,0.000535,0,0.003563,0,0.006687,0.006686,-0.008133,-0.008133,-0.000215,-0.000215,-0.001288,-0.001289,-0.000683,-0.000682,0.00057,0,0.182164,0,-0.091852,-0.091851,0.000126,0.000125,0,-0.000217,0,-0.000138,0,0.000776,0,0,-0.000404,0,0.000103,0.000103,-0.000406,0,0.000961,0.000962,-0.000982,0,0.000662,0.000662,-0.000612,-0.000612,-0.000407,0,0.000235
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M11] rank=11 service=ts-preserve-service metric=container.cpu.usage baseline=0.051549 peak=0.830183 signed_z=18.56 onset_bin=33 onset_rel_s=250.879 persistence_bins=3
values_compact=delta:0.031663,0.039547,0.039548,0,-0.073454,0,-0.006914,0,0.088676,0,-0.082506,0,-0.016781,0,0.085699,-0.041839,-0.041839,0,0.013287,0,0.098115,0,0,-0.099268,-0.010178,0,0.002826,0,0,-0.014546,0,-0.001591,0,0.409869,0.409869,-0.412586,-0.412586,0.000602,0.000602,0,-0.001218,-0.000487,-0.000487,0.001053,0.001052,0,0.001876,-0.001686,-0.001686,0.001872,0.001871,0.00128,0.001279,0,-0.000624,0.00138,0.001381,0.003295,0.003295,-0.008171,0,-0.003068,0.005663,0
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M12] rank=12 service=ts-travel-plan-service metric=container.memory.usage baseline=731904341.333333 peak=771981312.0 signed_z=18.263 onset_bin=42 onset_rel_s=318.28 persistence_bins=22
values_compact=delta:727597056,503808,233472,6799360,0,0,-2011136,483328,-2547712,-2547712,393216,393216,819200,819200,565248,0,546816,546816,-481280,-481280,372736,0,-757760,0,2273280,118784,0,49152,182272,182272,0,-233472,600064,600064,0,-258048,133120,133120,-112640,-112640,258048,0,36921344,-19185664,0,0,102400,0,-2048,-2048,-2048,-2048,4096,4096,-2048,-2048,47104,47104,2048,2048,129024,129024,-249856,0
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[279.3221526145935,479.29156398773193]

=== LOG SUMMARY ===
{"entries":[{"error_logs":2963,"error_pct":19.31,"service":"ts-seat-service","total_logs":15341},{"error_logs":302,"error_pct":16.09,"service":"ts-food-service","total_logs":1877},{"error_logs":94,"error_pct":5.06,"service":"ts-preserve-service","total_logs":1858},{"error_logs":93,"error_pct":1.6,"service":"ts-order-service","total_logs":5798},{"error_logs":66,"error_pct":25.19,"service":"ts-notification-service","total_logs":262},{"error_logs":65,"error_pct":24.81,"service":"ts-delivery-service","total_logs":262},{"error_logs":2,"error_pct":2.44,"service":"ts-inside-payment-service","total_logs":82},{"error_logs":1,"error_pct":2.44,"service":"ts-payment-service","total_logs":41}],"mode":"errors","omitted_services":23,"service_count":31}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":621405.2,"error_pct":7.69,"p95_during_ms":129500.7325725,"p95_pre_ms":20.8366291,"service":"ts-security-service","spans":1339},{"delta_pct":9524.1,"error_pct":10.34,"p95_during_ms":129534.82381660001,"p95_pre_ms":1345.936979,"service":"ts-preserve-service","spans":1180},{"delta_pct":485.9,"error_pct":0.0,"p95_during_ms":29.6700445,"p95_pre_ms":5.06406,"service":"ts-train-food-service","spans":2247},{"delta_pct":424.8,"error_pct":0.0,"p95_during_ms":24.15896139999999,"p95_pre_ms":4.603214499999999,"service":"ts-train-service","spans":9668},{"delta_pct":384.4,"error_pct":0.0,"p95_during_ms":234.25853004999973,"p95_pre_ms":48.36090755000001,"service":"ts-inside-payment-service","spans":604},{"delta_pct":309.7,"error_pct":0.0,"p95_during_ms":31.99354119999998,"p95_pre_ms":7.808175799999987,"service":"ts-contacts-service","spans":2862},{"delta_pct":273.0,"error_pct":0.0,"p95_during_ms":19.86188899999999,"p95_pre_ms":5.324520099999998,"service":"ts-order-service","spans":15416},{"delta_pct":228.0,"error_pct":0.0,"p95_during_ms":53.733311650000005,"p95_pre_ms":16.380356300000003,"service":"ts-payment-service","spans":395}],"omitted_services":22,"service_count":30}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=35 omitted_edges=3
[{"evidence_source":"metric","onset_rel_s":274.8,"rank":1,"service":"ts-food-service","severity_z":10.031},{"evidence_source":"metric","onset_rel_s":280.8,"rank":2,"service":"ts-ticket-office-service","severity_z":12.664},{"evidence_source":"trace","onset_rel_s":294.6,"rank":3,"service":"ts-security-service","severity_z":999.0},{"evidence_source":"trace","onset_rel_s":294.6,"rank":4,"service":"ts-preserve-service","severity_z":167.414},{"evidence_source":"trace","onset_rel_s":294.6,"rank":5,"service":"ts-ui-dashboard","severity_z":37.259},{"evidence_source":"trace","onset_rel_s":294.6,"rank":6,"service":"loadgenerator","severity_z":37.255},{"evidence_source":"metric","onset_rel_s":316.2,"rank":7,"service":"ts-travel-plan-service","severity_z":18.263},{"evidence_source":"metric","onset_rel_s":319.2,"rank":8,"service":"ts-news-service","severity_z":53.665},{"evidence_source":"metric","onset_rel_s":324.0,"rank":9,"service":"ts-avatar-service","severity_z":13.217},{"evidence_source":"trace","onset_rel_s":354.6,"rank":10,"service":"ts-travel-service","severity_z":21.534},{"evidence_source":"metric","onset_rel_s":391.2,"rank":11,"service":"ts-route-plan-service","severity_z":10.348},{"evidence_source":"metric","onset_rel_s":434.4,"rank":12,"service":"rabbitmq","severity_z":67.656},{"evidence_source":"trace","onset_rel_s":454.2,"rank":13,"service":"ts-travel2-service","severity_z":40.315},{"evidence_source":"none","onset_rel_s":null,"rank":14,"service":"ts-auth-service","severity_z":0.0}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"ts-ui-dashboard","caller":"loadgenerator"},{"callee":"ts-travel-service","caller":"ts-food-service"},{"callee":"ts-food-service","caller":"ts-preserve-service"},{"callee":"ts-security-service","caller":"ts-preserve-service"},{"callee":"ts-travel-service","caller":"ts-preserve-service"},{"callee":"ts-travel-service","caller":"ts-route-plan-service"},{"callee":"ts-travel2-service","caller":"ts-route-plan-service"},{"callee":"ts-route-plan-service","caller":"ts-travel-plan-service"},{"callee":"ts-auth-service","caller":"ts-ui-dashboard"},{"callee":"ts-food-service","caller":"ts-ui-dashboard"},{"callee":"ts-preserve-service","caller":"ts-ui-dashboard"},{"callee":"ts-travel-plan-service","caller":"ts-ui-dashboard"},{"callee":"ts-travel-service","caller":"ts-ui-dashboard"},{"callee":"ts-travel2-service","caller":"ts-ui-dashboard"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

[excluded before optimizer]

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
opaque_id: INC-2B53FEBACF6E
observation_window={"duration_rel_s":479.679,"source_metric_rows":1073}
selection_summary={"candidate_count":104,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":1000,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["loadgenerator","loadgenerator-b479bdc5c-dhqr6","mysql","mysql-0","rabbitmq","rabbitmq-0","ts-admin-basic-info-service","ts-admin-basic-info-service-96954787-mcwsz","ts-admin-order-service","ts-admin-order-service-6bcf6ddf78-nfd72","ts-admin-route-service","ts-admin-route-service-9678dfbb7-7ldcn","ts-admin-travel-service","ts-admin-travel-service-5f7dcc8c78-ln94h","ts-admin-user-service","ts-admin-user-service-5b6598696f-klgkm","ts-assurance-service","ts-assurance-service-5d8974b465-t92h9","ts-auth-service","ts-auth-service-6d4cb476f4-8qvb2","ts-avatar-service","ts-avatar-service-7d44f9cdb-x45h5","ts-basic-service","ts-basic-service-67bb4cc894-mrsvz","ts-cancel-service","ts-cancel-service-c464f54db-fbbwp","ts-config-service","ts-config-service-688bb57f66-pkhkb","ts-consign-price-service","ts-consign-price-service-7cd56448d5-n6h9x","ts-consign-service","ts-consign-service-858fd6988f-sbmhl","ts-contacts-service","ts-contacts-service-69f8874897-lxch4","ts-delivery-service","ts-delivery-service-8495b4886d-zf4j6","ts-execute-service","ts-execute-service-98d6db6b7-kqs6h","ts-food-delivery-service","ts-food-delivery-service-6965df9cb7-rllf6","ts-food-service","ts-food-service-5bc8874bdd-gd545","ts-gateway-service","ts-gateway-service-7646b44946-vchpg","ts-inside-payment-service","ts-inside-payment-service-7f65df9f55-nchvr","ts-news-service","ts-news-service-b7d748896-md8s6","ts-notification-service","ts-notification-service-7f945dc747-vl6bp","ts-order-other-service","ts-order-other-service-bdb88b855-j6dgf","ts-order-service","ts-order-service-6f4cfb5df7-2gjmg","ts-payment-service","ts-payment-service-767777d6bb-bg6nx","ts-preserve-other-service","ts-preserve-other-service-6cc7bb5679-db45v","ts-preserve-service","ts-preserve-service-c9c68bb7b-h8smw","ts-price-service","ts-price-service-75f657ff49-g2xdw","ts-rebook-service","ts-rebook-service-58c459f6d-fxg6w","ts-route-plan-service","ts-route-plan-service-6cb49854ff-rfhps","ts-route-service","ts-route-service-5495898fcc-c466v","ts-seat-service","ts-seat-service-695f74448f-b8zqd","ts-security-service","ts-security-service-67d6f6c4fd-kktwt","ts-station-food-service","ts-station-food-service-79b8d75b55-tv629","ts-station-service","ts-station-service-5747c84884-dlb4z","ts-ticket-office-service","ts-ticket-office-service-f4fcd85cf-76chr","ts-train-food-service","ts-train-food-service-cddfc5cd9-wqxtl","ts-train-service","ts-train-service-b7b76f69d-rw7gc","ts-travel-plan-service","ts-travel-plan-service-5c66f9b8dd-bl4sf","ts-travel-service","ts-travel-service-5d8d96b796-2z9w8","ts-travel2-service","ts-travel2-service-76d77f447d-np62f","ts-ui-dashboard","ts-ui-dashboard-677db5896c-dgqj2","ts-user-service","ts-user-service-8f5c8f8f5-g765w","ts-verification-code-service","ts-verification-code-service-7f9b649959-jp97q","ts-voucher-service","ts-voucher-service-f479849c9-4mbs9","ts-wait-order-service","ts-wait-order-service-67c96d8684-fjm2s","worker1","worker2","worker3","worker4","worker5","worker6"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[3.747,11.242,18.737,26.232,33.727,41.222,48.717,56.212,63.707,71.202,78.697,86.192,93.687,101.182,108.677,116.172,123.667,131.162,138.657,146.152,153.647,161.142,168.637,176.132,183.627,191.122,198.617,206.112,213.607,221.102,228.597,236.092,243.587,251.082,258.577,266.072,273.567,281.062,288.557,296.052,303.547,311.042,318.537,326.032,333.527,341.022,348.517,356.012,363.507,371.002,378.497,385.992,393.487,400.982,408.477,415.972,423.467,430.962,438.457,445.952,453.446,460.941,468.436,475.931]
[M1] rank=1 service=ts-consign-price-service-7cd56448d5-n6h9x metric=k8s.container.restarts baseline=0.0 peak=1.0 signed_z=999.0 onset_bin=34 onset_rel_s=258.577 persistence_bins=23
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0100010001000100010001000100010001000100010001000100010001000100
observed_counts_compact=csv:1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1
[M2] rank=2 service=ts-consign-price-service metric=container.memory.available baseline=2474206404.085106 peak=3220611072.0 signed_z=999.0 onset_bin=34 onset_rel_s=258.577 persistence_bins=30
values_compact=delta:2475114496,-94208,-94208,-143360,0,-4096,0,0,0,-749568,0,161792,161792,0,-118784,0,-262144,0,-98304,0,-4096,0,0,0,-49152,0,0,-57344,0,0,0,0,746848256,0,0,0,0,0,0,0,0,0,0,0,0,0,0,-6144,-6144,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0000000000000000000000000000000011000000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,0,0,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,2
[M3] rank=3 service=ts-consign-price-service metric=container.memory.rss baseline=736377834.212766 peak=311296.0 signed_z=-999.0 onset_bin=34 onset_rel_s=258.577 persistence_bins=30
values_compact=rle:735518720*1,735602688*1,735686656*1,735825920*2,735834112*4,736079872*2,736182272*1,736284672*2,736399360*2,736661504*2,736759808*2,736763904*4,736817152*3,736870400*5,null*2,311296*15,317440*1,323584*14
missing_mask_bits=0000000000000000000000000000000011000000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,0,0,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,2
[M4] rank=4 service=ts-consign-price-service metric=container.memory.usage baseline=747404091.914894 peak=614400.0 signed_z=-999.0 onset_bin=34 onset_rel_s=258.577 persistence_bins=30
values_compact=rle:746496000*1,746590208*1,746684416*1,746827776*2,746831872*4,747581440*2,747419648*1,747257856*2,747376640*2,747638784*2,747737088*2,747741184*4,747790336*3,747847680*5,null*2,614400*15,620544*1,626688*14
missing_mask_bits=0000000000000000000000000000000011000000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,0,0,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,2
[M5] rank=5 service=ts-consign-price-service metric=container.memory.working_set baseline=747019067.914894 peak=614400.0 signed_z=-999.0 onset_bin=32 onset_rel_s=243.587 persistence_bins=32
values_compact=rle:746110976*1,746205184*1,746299392*1,746442752*2,746446848*4,747196416*2,747034624*1,746872832*2,746991616*2,747253760*2,747352064*2,747356160*4,747405312*3,747462656*5,614400*17,620544*1,626688*14
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,2
[M6] rank=6 service=ts-consign-price-service metric=k8s.pod.memory.available baseline=2473524115.06383 peak=3219558400.0 signed_z=999.0 onset_bin=33 onset_rel_s=251.082 persistence_bins=31
values_compact=delta:2474475520,-49152,0,-165888,-165888,-4096,0,0,0,-677888,-677888,970752,0,-79872,-79872,-30720,-30720,-278528,-278528,0,253952,0,0,0,-49152,57344,57344,-86016,-86016,0,0,-196608,-196608,373438464,373438464,0,0,0,0,0,0,0,0,0,0,0,0,0,0,-6144,-6144,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,2
[M7] rank=7 service=ts-consign-price-service metric=k8s.pod.memory.node.utilization baseline=0.00554 peak=1.4e-05 signed_z=-999.0 onset_bin=33 onset_rel_s=251.082 persistence_bins=31
values_compact=rle:0.005533*3,0.005535*1,0.005536*5,0.005541*1,0.005546*1,0.005539*3,0.00554*3,0.005542*1,0.005545*2,0.005543*6,0.005542*1,0.005543*4,0.005545*1,0.005546*1,0.00278*1,0.000014*15,0.000015*15
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,2
[M8] rank=8 service=ts-consign-price-service metric=k8s.pod.memory.rss baseline=736399447.148936 peak=356352.0 signed_z=-999.0 onset_bin=33 onset_rel_s=251.082 persistence_bins=31
values_compact=delta:735514624,53248,0,151552,151552,8192,0,0,0,180224,180224,49152,0,77824,77824,30720,30720,149504,149504,0,4096,0,0,0,53248,-45056,-45056,71680,71680,0,0,77824,77824,-368357376,-368357376,0,0,0,0,0,0,0,0,0,0,0,0,0,0,6144,6144,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,2
[M9] rank=9 service=ts-consign-price-service metric=k8s.pod.memory.usage baseline=748086380.93617 peak=1953792.0 signed_z=-999.0 onset_bin=33 onset_rel_s=251.082 persistence_bins=31
values_compact=delta:747134976,49152,0,165888,165888,4096,0,0,0,677888,677888,-970752,0,79872,79872,30720,30720,278528,278528,0,-253952,0,0,0,49152,-57344,-57344,86016,86016,0,0,196608,196608,-373487616,-373487616,0,0,0,0,0,0,0,0,0,0,0,0,0,0,6144,6144,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,2
[M10] rank=10 service=ts-consign-price-service metric=k8s.pod.memory.working_set baseline=747701356.93617 peak=1667072.0 signed_z=-999.0 onset_bin=33 onset_rel_s=251.082 persistence_bins=31
values_compact=delta:746749952,49152,0,165888,165888,4096,0,0,0,677888,677888,-970752,0,79872,79872,30720,30720,278528,278528,0,-253952,0,0,0,49152,-57344,-57344,86016,86016,0,0,196608,196608,-373438464,-373438464,0,0,0,0,0,0,0,0,0,0,0,0,0,0,6144,6144,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,2
[M11] rank=11 service=ts-consign-price-service metric=k8s.pod.memory_limit_utilization baseline=0.232237 peak=0.000607 signed_z=-999.0 onset_bin=33 onset_rel_s=251.082 persistence_bins=31
values_compact=rle:0.231941*1,0.231956*2,0.232008*1,0.232059*1,0.232061*4,0.232271*1,0.232482*1,0.23218*2,0.232205*1,0.23223*1,0.232239*1,0.232249*1,0.232335*1,0.232422*2,0.232343*4,0.232358*1,0.23234*1,0.232323*1,0.232349*1,0.232376*3,0.232437*1,0.232498*1,0.116552*1,0.000607*15,0.000608*1,0.00061*14
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,2
[M12] rank=12 service=ts-consign-service metric=hubble_http_request_duration_p50_seconds baseline=0.008542 peak=3.75 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.011667,-0.004167,0,0.00375,-0.003333,-0.000417,0,0,0,0,3.7425,-1.87125,1.87125,-1.87375,0.0025,-0.0025
missing_mask_bits=1011101110111011101110111011101110111011101110111011101110111011
observed_counts_compact=csv:0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[236.81558656692505,476.8164613246918]

=== LOG SUMMARY ===
{"entries":[{"error_logs":4079,"error_pct":100.0,"service":"ts-ui-dashboard","total_logs":4079},{"error_logs":209,"error_pct":16.61,"service":"ts-food-service","total_logs":1258},{"error_logs":96,"error_pct":25.0,"service":"ts-delivery-service","total_logs":384},{"error_logs":95,"error_pct":25.0,"service":"ts-notification-service","total_logs":380},{"error_logs":45,"error_pct":5.27,"service":"ts-consign-service","total_logs":854},{"error_logs":39,"error_pct":1.09,"service":"ts-order-service","total_logs":3588},{"error_logs":39,"error_pct":2.81,"service":"ts-preserve-service","total_logs":1386}],"mode":"errors","omitted_services":24,"service_count":31}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":13520.0,"error_pct":29.41,"p95_during_ms":3556.9610725,"p95_pre_ms":26.11579549999999,"service":"ts-consign-service","spans":878},{"delta_pct":-92.2,"error_pct":0.0,"p95_during_ms":14.07068925,"p95_pre_ms":180.91796149999985,"service":"ts-payment-service","spans":150},{"delta_pct":56.6,"error_pct":0.0,"p95_during_ms":52.4960188,"p95_pre_ms":33.523671199999995,"service":"ts-inside-payment-service","spans":728},{"delta_pct":-23.8,"error_pct":0.0,"p95_during_ms":3.5538198,"p95_pre_ms":4.66367305,"service":"ts-price-service","spans":2625},{"delta_pct":-22.5,"error_pct":0.0,"p95_during_ms":3.4130514999999995,"p95_pre_ms":4.4022780500000005,"service":"ts-user-service","spans":3460},{"delta_pct":-17.8,"error_pct":0.0,"p95_during_ms":467.175616,"p95_pre_ms":568.597042249999,"service":"ts-travel-plan-service","spans":1473},{"delta_pct":-16.6,"error_pct":0.0,"p95_during_ms":3.1151351999999997,"p95_pre_ms":3.73469905,"service":"ts-station-service","spans":4775},{"delta_pct":-16.6,"error_pct":0.0,"p95_during_ms":4.843161,"p95_pre_ms":5.807085449999999,"service":"ts-train-food-service","spans":1341}],"omitted_services":22,"service_count":30}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=35 omitted_edges=0
[{"evidence_source":"trace","onset_rel_s":244.8,"rank":1,"service":"ts-security-service","severity_z":65.431},{"evidence_source":"metric","onset_rel_s":246.6,"rank":2,"service":"ts-consign-price-service","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":251.4,"rank":3,"service":"ts-user-service","severity_z":189.736},{"evidence_source":"metric","onset_rel_s":268.8,"rank":4,"service":"ts-notification-service","severity_z":81.521},{"evidence_source":"metric","onset_rel_s":273.6,"rank":5,"service":"ts-basic-service","severity_z":55.175},{"evidence_source":"trace","onset_rel_s":285.0,"rank":6,"service":"ts-consign-service","severity_z":405.45},{"evidence_source":"trace","onset_rel_s":285.0,"rank":7,"service":"loadgenerator","severity_z":357.703},{"evidence_source":"trace","onset_rel_s":285.0,"rank":8,"service":"ts-order-other-service","severity_z":77.555},{"evidence_source":"trace","onset_rel_s":315.0,"rank":9,"service":"ts-ui-dashboard","severity_z":271.542},{"evidence_source":"metric","onset_rel_s":321.0,"rank":10,"service":"ts-food-service","severity_z":22.488},{"evidence_source":"metric","onset_rel_s":356.4,"rank":11,"service":"ts-route-service","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":387.6,"rank":12,"service":"ts-seat-service","severity_z":58.252},{"evidence_source":"trace","onset_rel_s":424.8,"rank":13,"service":"ts-contacts-service","severity_z":3.112},{"evidence_source":"metric","onset_rel_s":447.6,"rank":14,"service":"ts-auth-service","severity_z":36.267}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"ts-ui-dashboard","caller":"loadgenerator"},{"callee":"ts-route-service","caller":"ts-basic-service"},{"callee":"ts-consign-price-service","caller":"ts-consign-service"},{"callee":"ts-order-other-service","caller":"ts-seat-service"},{"callee":"ts-order-other-service","caller":"ts-security-service"},{"callee":"ts-auth-service","caller":"ts-ui-dashboard"},{"callee":"ts-consign-service","caller":"ts-ui-dashboard"},{"callee":"ts-contacts-service","caller":"ts-ui-dashboard"},{"callee":"ts-food-service","caller":"ts-ui-dashboard"},{"callee":"ts-order-other-service","caller":"ts-ui-dashboard"},{"callee":"ts-route-service","caller":"ts-ui-dashboard"},{"callee":"ts-user-service","caller":"ts-ui-dashboard"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

{"confidence":"high","reason":"Rank ts-consign-price-service first because ts-consign-price-service has direct k8s.container.restarts evidence (signed-z 999, persistence 23 bins); although ts-consign-service is salient, the caller path ts-consign-service -> ts-consign-price-service means a disturbance in the callee can propagate back toward that caller-side symptom. The remaining entries preserve evidence-supported alternatives so the ranking retains calibrated uncertainty instead of collapsing to one answer.","services":["ts-consign-price-service","ts-consign-service","ts-ui-dashboard","loadgenerator","ts-security-service"]}

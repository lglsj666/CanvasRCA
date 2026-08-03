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
opaque_id: INC-5D4F54681BC3
observation_window={"duration_rel_s":479.357,"source_metric_rows":952}
selection_summary={"candidate_count":104,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":901,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["loadgenerator","loadgenerator-d75cc479f-zrzrg","mysql","mysql-0","rabbitmq","rabbitmq-0","ts-admin-basic-info-service","ts-admin-basic-info-service-66cdcc94bc-tplt8","ts-admin-order-service","ts-admin-order-service-5b6dc77d7d-pd8gf","ts-admin-route-service","ts-admin-route-service-f9c84f85f-j8hm2","ts-admin-travel-service","ts-admin-travel-service-659b5c9df4-7gn89","ts-admin-user-service","ts-admin-user-service-5bfc8844b9-w9jld","ts-assurance-service","ts-assurance-service-75c854dc5c-hs5df","ts-auth-service","ts-auth-service-69bdd5df8-bx4nv","ts-avatar-service","ts-avatar-service-845b64df6-8vqj9","ts-basic-service","ts-basic-service-7c6d59d5c4-hx2wv","ts-cancel-service","ts-cancel-service-7ffd988fdb-c4254","ts-config-service","ts-config-service-55cffbf48b-gzhkj","ts-consign-price-service","ts-consign-price-service-654cb4fc65-5wpx4","ts-consign-service","ts-consign-service-9954fddf-hwk8g","ts-contacts-service","ts-contacts-service-6d745b6c8f-qlffm","ts-delivery-service","ts-delivery-service-694895c6cb-ccmhn","ts-execute-service","ts-execute-service-8457c56cb7-rkqbt","ts-food-delivery-service","ts-food-delivery-service-96d856899-bcbzr","ts-food-service","ts-food-service-64d454885b-rsg62","ts-gateway-service","ts-gateway-service-7f988fb8c4-f4gkc","ts-inside-payment-service","ts-inside-payment-service-5ccb8ccb87-cqkqb","ts-news-service","ts-news-service-6d6c6d7855-bgzzj","ts-notification-service","ts-notification-service-58f6c468d7-gbrbk","ts-order-other-service","ts-order-other-service-5d6878687f-j4cgm","ts-order-service","ts-order-service-6794d6f564-5bshm","ts-payment-service","ts-payment-service-58854d694-b654q","ts-preserve-other-service","ts-preserve-other-service-64fd9c88cf-h6mbq","ts-preserve-service","ts-preserve-service-696df489d4-j5kg9","ts-price-service","ts-price-service-67c895b45-gtnjq","ts-rebook-service","ts-rebook-service-7c7644bbdd-lvmbx","ts-route-plan-service","ts-route-plan-service-556cddc5c9-khq8g","ts-route-service","ts-route-service-cfc6dbcf7-4jrld","ts-seat-service","ts-seat-service-6c78b7d797-dq2q6","ts-security-service","ts-security-service-55f5b777bb-nnx6f","ts-station-food-service","ts-station-food-service-746f6779d7-qmv84","ts-station-service","ts-station-service-65986cc944-mh69r","ts-ticket-office-service","ts-ticket-office-service-d7c58b8c7-smj4v","ts-train-food-service","ts-train-food-service-d5485c677-d47lk","ts-train-service","ts-train-service-9b56d75b6-cqtdw","ts-travel-plan-service","ts-travel-plan-service-7875c49896-mgjj4","ts-travel-service","ts-travel-service-c7b5c6d9b-sx826","ts-travel2-service","ts-travel2-service-7ff5bbbf54-52h5s","ts-ui-dashboard","ts-ui-dashboard-57867cb85c-kxq59","ts-user-service","ts-user-service-54dd6b48c-ccbgw","ts-verification-code-service","ts-verification-code-service-85785c4f79-7n2p6","ts-voucher-service","ts-voucher-service-689c4fc885-6kcbv","ts-wait-order-service","ts-wait-order-service-7cf6bc9468-ppbvr","worker1","worker2","worker3","worker4","worker5","worker6"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[3.745,11.235,18.725,26.215,33.705,41.195,48.685,56.175,63.665,71.155,78.645,86.135,93.624,101.114,108.604,116.094,123.584,131.074,138.564,146.054,153.544,161.034,168.524,176.014,183.504,190.994,198.484,205.974,213.464,220.954,228.444,235.934,243.424,250.914,258.404,265.893,273.383,280.873,288.363,295.853,303.343,310.833,318.323,325.813,333.303,340.793,348.283,355.773,363.263,370.753,378.243,385.733,393.223,400.713,408.203,415.693,423.183,430.673,438.163,445.652,453.142,460.632,468.122,475.612]
[M1] rank=1 service=ts-admin-route-service metric=k8s.pod.memory.rss baseline=674858837.333333 peak=669974528.0 signed_z=-74.846 onset_bin=38 onset_rel_s=288.363 persistence_bins=26
values_compact=rle:674852864*2,674856960*4,674916352*1,674975744*5,674940928*1,674906112*2,674840576*2,674844672*3,674816000*1,674787328*5,674795520*1,674803712*11,669974528*7,669978624*9,669999104*7,670076928*3
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1
[M2] rank=2 service=ts-admin-route-service metric=container.memory.rss baseline=674820522.666667 peak=669933568.0 signed_z=-69.592 onset_bin=36 onset_rel_s=273.383 persistence_bins=28
values_compact=rle:674811904*1,674816000*4,674934784*8,674799616*2,674803712*5,674775040*1,674746368*5,674754560*1,674762752*9,672348160*1,669933568*8,669937664*9,669947904*1,669958144*7,670035968*2
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1
[M3] rank=3 service=ts-admin-route-service metric=k8s.pod.memory.available baseline=2535440298.666667 peak=2540351488.0 signed_z=57.171 onset_bin=38 onset_rel_s=288.363 persistence_bins=26
values_compact=delta:2535407616,0,-4096,0,0,0,-51200,-51200,0,0,0,0,36864,36864,0,114688,0,-4096,0,0,24576,24576,0,0,0,0,-8192,-8192,0,0,8192,0,0,0,0,0,0,0,4820992,0,0,0,0,0,0,4096,0,0,0,0,0,0,0,0,-20480,0,0,0,0,0,0,-118784,0,0
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1
[M4] rank=4 service=ts-admin-route-service metric=k8s.pod.memory.usage baseline=686170197.333333 peak=681259008.0 signed_z=-57.171 onset_bin=38 onset_rel_s=288.363 persistence_bins=26
values_compact=rle:686202880*2,686206976*4,686258176*1,686309376*5,686272512*1,686235648*2,686120960*2,686125056*3,686100480*1,686075904*5,686084096*1,686092288*3,686084096*8,681263104*7,681259008*9,681279488*7,681398272*3
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1
[M5] rank=5 service=ts-admin-route-service metric=k8s.pod.memory.working_set baseline=685785173.333333 peak=680873984.0 signed_z=-57.171 onset_bin=38 onset_rel_s=288.363 persistence_bins=26
values_compact=rle:685817856*2,685821952*4,685873152*1,685924352*5,685887488*1,685850624*2,685735936*2,685740032*3,685715456*1,685690880*5,685699072*1,685707264*3,685699072*8,680878080*7,680873984*9,680894464*7,681013248*3
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1
[M6] rank=6 service=ts-admin-route-service metric=k8s.pod.memory_limit_utilization baseline=0.213015 peak=0.211491 signed_z=-57.171 onset_bin=38 onset_rel_s=288.363 persistence_bins=26
values_compact=rle:0.213025*2,0.213027*4,0.213043*1,0.213058*5,0.213047*1,0.213036*2,0.213*2,0.213001*3,0.212994*1,0.212986*5,0.212989*1,0.212991*3,0.212989*8,0.211492*7,0.211491*9,0.211497*7,0.211534*3
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1
[M7] rank=7 service=ts-admin-route-service metric=k8s.pod.memory.node.utilization baseline=0.005082 peak=0.005045 signed_z=-57.171 onset_bin=38 onset_rel_s=288.363 persistence_bins=26
values_compact=rle:0.005082*7,0.005083*5,0.005082*3,0.005081*23,0.005045*23,0.005046*3
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1
[M8] rank=8 service=ts-admin-route-service metric=container.memory.available baseline=2536129280.0 peak=2541039616.0 signed_z=53.958 onset_bin=36 onset_rel_s=273.383 persistence_bins=28
values_compact=delta:2536095744,-4096,0,0,0,-102400,0,0,0,0,0,0,0,188416,0,-4096,0,0,0,0,24576,24576,0,0,0,0,-8192,-8192,0,0,4096,4096,0,0,0,0,2410496,2410496,0,0,0,0,0,0,0,4096,0,0,0,0,0,0,0,0,-10240,-10240,0,0,0,0,0,0,-118784,0
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1
[M9] rank=9 service=ts-admin-route-service metric=container.memory.usage baseline=685481216.0 peak=680570880.0 signed_z=-53.958 onset_bin=36 onset_rel_s=273.383 persistence_bins=28
values_compact=rle:685514752*1,685518848*4,685621248*8,685432832*2,685436928*5,685412352*1,685387776*5,685395968*1,685404160*3,685400064*1,685395968*5,682985472*1,680574976*8,680570880*9,680581120*1,680591360*7,680710144*2
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1
[M10] rank=10 service=ts-admin-route-service metric=container.memory.working_set baseline=685096192.0 peak=680185856.0 signed_z=-53.958 onset_bin=36 onset_rel_s=273.383 persistence_bins=28
values_compact=rle:685129728*1,685133824*4,685236224*8,685047808*2,685051904*5,685027328*1,685002752*5,685010944*1,685019136*3,685015040*1,685010944*5,682600448*1,680189952*8,680185856*9,680196096*1,680206336*7,680325120*2
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1
[M11] rank=11 service=ts-avatar-service metric=k8s.pod.memory.rss baseline=179552938.666667 peak=182112256.0 signed_z=30.647 onset_bin=34 onset_rel_s=258.404 persistence_bins=30
values_compact=delta:179294208,167936,0,0,28672,0,0,0,0,0,0,16384,0,0,0,0,0,43008,43008,20480,0,12288,0,0,0,0,0,0,24576,0,0,69632,0,0,352256,0,8192,0,4096,0,0,0,0,0,4096,0,0,0,0,0,0,0,163840,0,0,8192,0,983040,0,0,0,868352,0,0
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M12] rank=12 service=ts-avatar-service metric=k8s.pod.memory.page_faults baseline=49789.166667 peak=50377.0 signed_z=28.832 onset_bin=34 onset_rel_s=258.404 persistence_bins=30
values_compact=rle:49726*1,49767*3,49774*7,49778*6,49788.5*1,49799*1,49804*2,49807*7,49813*3,49830*3,49916*2,49918*2,49919*6,50335*8,50375*3,50377*9
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[270.92378759384155,475.98725509643555]

=== LOG SUMMARY ===
{"entries":[{"error_logs":3782,"error_pct":19.32,"service":"ts-seat-service","total_logs":19574},{"error_logs":410,"error_pct":16.58,"service":"ts-food-service","total_logs":2473},{"error_logs":122,"error_pct":5.15,"service":"ts-preserve-service","total_logs":2369},{"error_logs":112,"error_pct":1.6,"service":"ts-order-service","total_logs":7015},{"error_logs":96,"error_pct":25.0,"service":"ts-delivery-service","total_logs":384},{"error_logs":96,"error_pct":25.0,"service":"ts-notification-service","total_logs":384}],"mode":"errors","omitted_services":25,"service_count":31}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":34033.2,"error_pct":57.89,"p95_during_ms":130992.0522124,"p95_pre_ms":383.7671736999998,"service":"ts-preserve-service","spans":1560},{"delta_pct":469.1,"error_pct":0.0,"p95_during_ms":28.588504099999998,"p95_pre_ms":5.023616,"service":"ts-train-food-service","spans":2933},{"delta_pct":291.9,"error_pct":0.0,"p95_during_ms":13.434690199999974,"p95_pre_ms":3.42801155,"service":"ts-station-service","spans":9515},{"delta_pct":206.2,"error_pct":0.0,"p95_during_ms":12.002450850000006,"p95_pre_ms":3.91921955,"service":"ts-price-service","spans":5270},{"delta_pct":175.7,"error_pct":0.0,"p95_during_ms":9.22491994999999,"p95_pre_ms":3.3457409999999994,"service":"ts-config-service","spans":18910},{"delta_pct":158.5,"error_pct":0.0,"p95_during_ms":83.44142419999997,"p95_pre_ms":32.2814215,"service":"ts-food-service","spans":2605},{"delta_pct":151.1,"error_pct":0.0,"p95_during_ms":32.380842149999985,"p95_pre_ms":12.8945056,"service":"ts-seat-service","spans":15626},{"delta_pct":138.9,"error_pct":0.0,"p95_during_ms":9.02048359999997,"p95_pre_ms":3.776205749999998,"service":"ts-user-service","spans":7770}],"omitted_services":22,"service_count":30}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=35 omitted_edges=3
[{"evidence_source":"trace","onset_rel_s":284.4,"rank":1,"service":"ts-ui-dashboard","severity_z":254.914},{"evidence_source":"metric","onset_rel_s":286.2,"rank":2,"service":"ts-admin-route-service","severity_z":74.846},{"evidence_source":"trace","onset_rel_s":324.6,"rank":3,"service":"loadgenerator","severity_z":242.103},{"evidence_source":"trace","onset_rel_s":324.6,"rank":4,"service":"ts-seat-service","severity_z":135.383},{"evidence_source":"trace","onset_rel_s":374.4,"rank":5,"service":"ts-travel-plan-service","severity_z":75.819},{"evidence_source":"trace","onset_rel_s":384.6,"rank":6,"service":"ts-price-service","severity_z":335.933},{"evidence_source":"trace","onset_rel_s":384.6,"rank":7,"service":"ts-config-service","severity_z":85.477},{"evidence_source":"trace","onset_rel_s":384.6,"rank":8,"service":"ts-train-service","severity_z":69.48},{"evidence_source":"trace","onset_rel_s":394.2,"rank":9,"service":"ts-station-service","severity_z":310.584},{"evidence_source":"trace","onset_rel_s":394.2,"rank":10,"service":"ts-train-food-service","severity_z":226.518},{"evidence_source":"trace","onset_rel_s":404.4,"rank":11,"service":"ts-order-other-service","severity_z":999.0},{"evidence_source":"trace","onset_rel_s":404.4,"rank":12,"service":"ts-food-service","severity_z":755.105},{"evidence_source":"trace","onset_rel_s":404.4,"rank":13,"service":"ts-travel2-service","severity_z":161.954},{"evidence_source":"trace","onset_rel_s":404.4,"rank":14,"service":"ts-travel-service","severity_z":144.24}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"ts-ui-dashboard","caller":"loadgenerator"},{"callee":"ts-train-food-service","caller":"ts-food-service"},{"callee":"ts-travel-service","caller":"ts-food-service"},{"callee":"ts-config-service","caller":"ts-seat-service"},{"callee":"ts-order-other-service","caller":"ts-seat-service"},{"callee":"ts-seat-service","caller":"ts-travel-plan-service"},{"callee":"ts-train-service","caller":"ts-travel-plan-service"},{"callee":"ts-seat-service","caller":"ts-travel-service"},{"callee":"ts-seat-service","caller":"ts-travel2-service"},{"callee":"ts-food-service","caller":"ts-ui-dashboard"},{"callee":"ts-order-other-service","caller":"ts-ui-dashboard"},{"callee":"ts-train-service","caller":"ts-ui-dashboard"},{"callee":"ts-travel-plan-service","caller":"ts-ui-dashboard"},{"callee":"ts-travel-service","caller":"ts-ui-dashboard"},{"callee":"ts-travel2-service","caller":"ts-ui-dashboard"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

[excluded before optimizer]

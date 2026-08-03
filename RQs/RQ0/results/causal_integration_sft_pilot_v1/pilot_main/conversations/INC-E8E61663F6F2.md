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
opaque_id: INC-E8E61663F6F2
observation_window={"duration_rel_s":478.591,"source_metric_rows":948}
selection_summary={"candidate_count":104,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":905,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["loadgenerator","loadgenerator-5867cb5967-tpdmw","mysql","mysql-0","rabbitmq","rabbitmq-0","ts-admin-basic-info-service","ts-admin-basic-info-service-6659d9d49-fvcvg","ts-admin-order-service","ts-admin-order-service-74874bb64-8nzww","ts-admin-route-service","ts-admin-route-service-bfb45ff69-24km5","ts-admin-travel-service","ts-admin-travel-service-685895dffb-nw8s8","ts-admin-user-service","ts-admin-user-service-7c45675555-mmpdn","ts-assurance-service","ts-assurance-service-76459f5575-rq59w","ts-auth-service","ts-auth-service-5c98dd7948-7b59q","ts-avatar-service","ts-avatar-service-868fb4bf7d-clcjx","ts-basic-service","ts-basic-service-5cdf66d69b-kkxxg","ts-cancel-service","ts-cancel-service-55ccd7978d-52j6n","ts-config-service","ts-config-service-b9bcfbc56-d2ck2","ts-consign-price-service","ts-consign-price-service-6749d49475-78jbc","ts-consign-service","ts-consign-service-b74f9b59f-gsltc","ts-contacts-service","ts-contacts-service-848bdcc799-jsgqg","ts-delivery-service","ts-delivery-service-6f79457966-hfbj9","ts-execute-service","ts-execute-service-5dbbc755fc-xqn9k","ts-food-delivery-service","ts-food-delivery-service-74ffc6dbb9-799sg","ts-food-service","ts-food-service-66b764476b-6rkbk","ts-gateway-service","ts-gateway-service-785597f976-c2zks","ts-inside-payment-service","ts-inside-payment-service-655f955977-tqxps","ts-news-service","ts-news-service-7869d45c45-p4ln9","ts-notification-service","ts-notification-service-55b4f48c8f-wm2gf","ts-order-other-service","ts-order-other-service-677c8677b5-q4dnd","ts-order-service","ts-order-service-5db685fb54-rkdpj","ts-payment-service","ts-payment-service-58fff7fd68-h5cxm","ts-preserve-other-service","ts-preserve-other-service-745ffd9f57-lznnc","ts-preserve-service","ts-preserve-service-79b467b6c8-4qsb2","ts-price-service","ts-price-service-fcbdb55f5-qmdc2","ts-rebook-service","ts-rebook-service-67f4f4986-nd7ng","ts-route-plan-service","ts-route-plan-service-6b4859cf65-v7ghk","ts-route-service","ts-route-service-757558799f-jzjhg","ts-seat-service","ts-seat-service-8959d487f-8jstt","ts-security-service","ts-security-service-5fbb5c757b-plw9q","ts-station-food-service","ts-station-food-service-864c57dbc7-4frst","ts-station-service","ts-station-service-774c9cb8b-2v54k","ts-ticket-office-service","ts-ticket-office-service-8687d77bc5-mqnvg","ts-train-food-service","ts-train-food-service-64c578fd99-d7mr4","ts-train-service","ts-train-service-7575645468-ptzwj","ts-travel-plan-service","ts-travel-plan-service-6c75975898-hpk5l","ts-travel-service","ts-travel-service-765c9c9858-7b4sv","ts-travel2-service","ts-travel2-service-5b97989896-xpf52","ts-ui-dashboard","ts-ui-dashboard-69f886fc55-jrwkl","ts-user-service","ts-user-service-d5b9d4bb9-bmcjr","ts-verification-code-service","ts-verification-code-service-57566595bf-72kfb","ts-voucher-service","ts-voucher-service-69d7fdccff-d6vvh","ts-wait-order-service","ts-wait-order-service-7c88777746-wws95","worker1","worker2","worker3","worker4","worker5","worker6"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[3.739,11.217,18.695,26.173,33.651,41.129,48.607,56.085,63.563,71.041,78.519,85.997,93.475,100.953,108.431,115.909,123.387,130.865,138.343,145.821,153.299,160.777,168.255,175.733,183.211,190.689,198.167,205.645,213.123,220.601,228.079,235.557,243.035,250.513,257.991,265.469,272.947,280.425,287.903,295.381,302.859,310.337,317.815,325.293,332.771,340.249,347.727,355.205,362.683,370.161,377.639,385.117,392.594,400.072,407.55,415.028,422.506,429.984,437.462,444.94,452.418,459.896,467.374,474.852]
[M1] rank=1 service=ts-route-service-757558799f-jzjhg metric=k8s.container.ready baseline=1.0 peak=0.0 signed_z=-999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,-1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=1000100010001000100010001000100010001000100010001000100010001000
observed_counts_compact=csv:0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1
[M2] rank=2 service=ts-route-service-757558799f-jzjhg metric=k8s.container.restarts baseline=0.0 peak=1.0 signed_z=999.0 onset_bin=37 onset_rel_s=280.425 persistence_bins=21
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=1000100010001000100010001000100010001000100010001000100010001000
observed_counts_compact=csv:0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1
[M3] rank=3 service=ts-route-service metric=k8s.deployment.available baseline=1.0 peak=0.0 signed_z=-999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,-1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=1000100010001000100010001000100010001000100010001000100010001000
observed_counts_compact=csv:0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1
[M4] rank=4 service=ts-route-service metric=k8s.pod.memory.major_page_faults baseline=0.0 peak=1.0 signed_z=999.0 onset_bin=35 onset_rel_s=265.469 persistence_bins=29
values_compact=rle:0*34,null*1,1*29
missing_mask_bits=0000000000000000000000000000000000100000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,0,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M5] rank=5 service=ts-route-service metric=container.filesystem.usage baseline=466944.0 peak=3080192.0 signed_z=848.404 onset_bin=32 onset_rel_s=243.035 persistence_bins=7
values_compact=rle:466944*32,3080192*2,null*1,69632*2,256000*1,442368*2,466944*24
missing_mask_bits=0000000000000000000000000000000000100000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,0,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M6] rank=6 service=rabbitmq metric=k8s.pod.memory.rss baseline=151279530.666667 peak=149852160.0 signed_z=-697.564 onset_bin=35 onset_rel_s=265.469 persistence_bins=26
values_compact=rle:151277568*17,151281664*18,149852160*2,150566912*1,151281664*3,151285760*23
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M7] rank=7 service=ts-route-service metric=k8s.pod.memory.page_faults baseline=160018.583333 peak=603316.0 signed_z=310.18 onset_bin=35 onset_rel_s=265.469 persistence_bins=29
values_compact=delta:156734,0,262,0,2219,0,0,236,51,0,0,772,0,34.5,34.5,22,22,0,49,4,4,0,73,0,6,432.5,432.5,1,0,18,1012,0,839,0,283850,26662,1727.5,1727.5,33157,33157,19857.5,19857.5,3486.5,3486.5,566.5,566.5,145.5,145.5,312,1347,94,94,243.5,243.5,0,1193,0,0,4055,3599,0,484,0
missing_mask_bits=0000000000000000000000000000000000100000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,0,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M8] rank=8 service=ts-route-service metric=k8s.pod.memory.node.utilization baseline=0.006099 peak=6e-06 signed_z=-128.849 onset_bin=35 onset_rel_s=265.469 persistence_bins=29
values_compact=delta:0.005999,0,0.000005,0,0.00007,0,0,0.000005,0.000003,0,0,0.000023,0,-0.000001,0,0,0.000001,0,0.000003,0,0,0,0.000001,0,0.000002,0.000019,0.00002,-0.000002,0,0,0.000046,0,-0.000026,0,-0.006162,0.002084,0.000093,0.000092,0.001145,0.001145,0.000468,0.000468,0.000061,0.000062,0.000022,0.000023,-0.000002,-0.000001,0.000015,-0.000013,0.000003,0.000002,0.000016,0.000015,0,0.000033,0,0,0.000126,-0.00003,0,0.000012,0
missing_mask_bits=0000000000000000000000000000000000100000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,0,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M9] rank=9 service=ts-route-service metric=k8s.pod.memory.usage baseline=823555072.0 peak=823296.0 signed_z=-128.849 onset_bin=35 onset_rel_s=265.469 persistence_bins=29
values_compact=delta:809979904,0,782336,0,9363456,0,0,692224,376832,0,0,3108864,0,-47104,-47104,59392,59392,0,421888,-2048,-2048,0,200704,0,258048,2592768,2592768,-266240,0,49152,6197248,0,-3448832,0,-832098304,281391104,12505088,12505088,154626048,154626048,63170560,63170560,8267776,8267776,3039232,3039232,-176128,-176128,1974272,-1703936,364544,364544,2080768,2080768,0,4485120,0,0,16969728,-4034560,0,1626112,0
missing_mask_bits=0000000000000000000000000000000000100000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,0,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M10] rank=10 service=ts-route-service metric=k8s.pod.memory_limit_utilization baseline=0.255665 peak=0.000256 signed_z=-128.849 onset_bin=35 onset_rel_s=265.469 persistence_bins=29
values_compact=delta:0.251451,0,0.000243,0,0.002907,0,0,0.000214,0.000117,0,0,0.000966,0,-0.000015,-0.000015,0.000019,0.000018,0,0.000131,-0.000001,0,0,0.000062,0,0.00008,0.000805,0.000805,-0.000083,0,0.000016,0.001924,0,-0.001071,0,-0.258317,0.087355,0.003882,0.003882,0.048002,0.048003,0.01961,0.019611,0.002567,0.002566,0.000944,0.000943,-0.000054,-0.000055,0.000613,-0.000529,0.000113,0.000113,0.000646,0.000646,0,0.001392,0,0,0.005269,-0.001253,0,0.000505,0
missing_mask_bits=0000000000000000000000000000000000100000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,0,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M11] rank=11 service=ts-route-service metric=k8s.pod.memory.available baseline=2398055424.0 peak=3220512768.0 signed_z=128.806 onset_bin=35 onset_rel_s=265.469 persistence_bins=29
values_compact=delta:2411630592,0,-782336,0,-9363456,0,0,-692224,-376832,0,0,-3108864,0,47104,47104,-59392,-59392,0,-421888,2048,2048,0,-200704,0,-258048,-2592768,-2592768,266240,0,-49152,-6197248,0,3416064,0,831856640,-281358336,-12328960,-12328960,-154626048,-154626048,-63170560,-63170560,-8267776,-8267776,-3039232,-3039232,176128,176128,-1974272,1703936,-364544,-364544,-2080768,-2080768,0,-4485120,0,0,-16969728,4034560,0,-1626112,0
missing_mask_bits=0000000000000000000000000000000000100000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,0,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M12] rank=12 service=ts-route-service metric=k8s.pod.memory.working_set baseline=823170048.0 peak=712704.0 signed_z=-128.806 onset_bin=35 onset_rel_s=265.469 persistence_bins=29
values_compact=delta:809594880,0,782336,0,9363456,0,0,692224,376832,0,0,3108864,0,-47104,-47104,59392,59392,0,421888,-2048,-2048,0,200704,0,258048,2592768,2592768,-266240,0,49152,6197248,0,-3416064,0,-831856640,281358336,12328960,12328960,154626048,154626048,63170560,63170560,8267776,8267776,3039232,3039232,-176128,-176128,1974272,-1703936,364544,364544,2080768,2080768,0,4485120,0,0,16969728,-4034560,0,1626112,0
missing_mask_bits=0000000000000000000000000000000000100000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,0,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[258.59124279022217,478.5913815498352]

=== LOG SUMMARY ===
{"entries":[{"error_logs":3556,"error_pct":19.29,"service":"ts-seat-service","total_logs":18438},{"error_logs":442,"error_pct":4.09,"service":"ts-ui-dashboard","total_logs":10815},{"error_logs":379,"error_pct":16.82,"service":"ts-food-service","total_logs":2253},{"error_logs":118,"error_pct":1.66,"service":"ts-order-service","total_logs":7117},{"error_logs":118,"error_pct":5.23,"service":"ts-preserve-service","total_logs":2257},{"error_logs":65,"error_pct":25.0,"service":"ts-notification-service","total_logs":260},{"error_logs":63,"error_pct":25.3,"service":"ts-delivery-service","total_logs":249},{"error_logs":10,"error_pct":100.0,"service":"mysql","total_logs":10}],"mode":"errors","omitted_services":24,"service_count":32}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":142.8,"error_pct":0.0,"p95_during_ms":43.095415800000026,"p95_pre_ms":17.746375800000003,"service":"ts-seat-service","spans":14719},{"delta_pct":140.1,"error_pct":0.0,"p95_during_ms":11.356671250000012,"p95_pre_ms":4.7297903499999965,"service":"ts-order-other-service","spans":11610},{"delta_pct":118.7,"error_pct":0.0,"p95_during_ms":84.50012389999996,"p95_pre_ms":38.63553759999995,"service":"ts-basic-service","spans":7938},{"delta_pct":109.1,"error_pct":0.0,"p95_during_ms":9.817353099999988,"p95_pre_ms":4.695441700000001,"service":"ts-station-service","spans":9085},{"delta_pct":100.7,"error_pct":0.0,"p95_during_ms":14.812827199999989,"p95_pre_ms":7.379454099999992,"service":"ts-contacts-service","spans":3475},{"delta_pct":94.1,"error_pct":0.0,"p95_during_ms":50.596420649999914,"p95_pre_ms":26.071197799999993,"service":"ts-security-service","spans":1650},{"delta_pct":-91.5,"error_pct":0.0,"p95_during_ms":99.4946284499998,"p95_pre_ms":1171.6878578,"service":"ts-food-service","spans":2349},{"delta_pct":83.7,"error_pct":0.0,"p95_during_ms":9.445148,"p95_pre_ms":5.142877599999999,"service":"ts-order-service","spans":18806}],"omitted_services":22,"service_count":30}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=35 omitted_edges=0
[{"evidence_source":"metric","onset_rel_s":262.8,"rank":1,"service":"rabbitmq","severity_z":697.564},{"evidence_source":"metric","onset_rel_s":285.6,"rank":2,"service":"ts-cancel-service","severity_z":51.861},{"evidence_source":"trace","onset_rel_s":313.8,"rank":3,"service":"ts-route-service","severity_z":45.27},{"evidence_source":"trace","onset_rel_s":313.8,"rank":4,"service":"ts-order-other-service","severity_z":72.28},{"evidence_source":"trace","onset_rel_s":313.8,"rank":5,"service":"ts-price-service","severity_z":70.195},{"evidence_source":"trace","onset_rel_s":313.8,"rank":6,"service":"ts-order-service","severity_z":54.924},{"evidence_source":"trace","onset_rel_s":313.8,"rank":7,"service":"ts-contacts-service","severity_z":53.986},{"evidence_source":"metric","onset_rel_s":320.4,"rank":8,"service":"mysql","severity_z":30.472},{"evidence_source":"trace","onset_rel_s":324.0,"rank":9,"service":"ts-config-service","severity_z":73.14},{"evidence_source":"trace","onset_rel_s":324.0,"rank":10,"service":"ts-station-service","severity_z":59.786},{"evidence_source":"trace","onset_rel_s":324.0,"rank":11,"service":"ts-train-food-service","severity_z":58.358},{"evidence_source":"trace","onset_rel_s":324.0,"rank":12,"service":"ts-train-service","severity_z":53.37},{"evidence_source":"trace","onset_rel_s":324.0,"rank":13,"service":"ts-station-food-service","severity_z":24.542},{"evidence_source":"trace","onset_rel_s":334.2,"rank":14,"service":"ts-user-service","severity_z":142.772}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"ts-order-service","caller":"ts-cancel-service"},{"callee":"ts-user-service","caller":"ts-cancel-service"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

{"confidence":"medium","reason":"Rank ts-route-service first because ts-route-service has direct k8s.container.ready evidence (signed-z -999, persistence 0 bins); rabbitmq is second despite propagation rank 1 because onset ordering alone does not establish the causal origin.","services":["ts-route-service","rabbitmq"]}

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
opaque_id: INC-EAB3A0BD0F19
observation_window={"duration_rel_s":479.418,"source_metric_rows":952}
selection_summary={"candidate_count":104,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":910,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["loadgenerator","loadgenerator-77d5b896cb-d7fjd","mysql","mysql-0","rabbitmq","rabbitmq-0","ts-admin-basic-info-service","ts-admin-basic-info-service-66cdcc94bc-czvwt","ts-admin-order-service","ts-admin-order-service-5b6dc77d7d-dcnxd","ts-admin-route-service","ts-admin-route-service-f9c84f85f-fhs52","ts-admin-travel-service","ts-admin-travel-service-659b5c9df4-hl8wm","ts-admin-user-service","ts-admin-user-service-5bfc8844b9-kvm4h","ts-assurance-service","ts-assurance-service-75c854dc5c-dn7bd","ts-auth-service","ts-auth-service-69bdd5df8-tkr9v","ts-avatar-service","ts-avatar-service-845b64df6-hnkfg","ts-basic-service","ts-basic-service-7c6d59d5c4-kq255","ts-cancel-service","ts-cancel-service-7ffd988fdb-wmz8k","ts-config-service","ts-config-service-55cffbf48b-mg9fm","ts-consign-price-service","ts-consign-price-service-654cb4fc65-2wnfq","ts-consign-service","ts-consign-service-9954fddf-jtsg6","ts-contacts-service","ts-contacts-service-6d745b6c8f-rw7ww","ts-delivery-service","ts-delivery-service-694895c6cb-dvr8n","ts-execute-service","ts-execute-service-8457c56cb7-zv9pg","ts-food-delivery-service","ts-food-delivery-service-96d856899-rs8pl","ts-food-service","ts-food-service-64d454885b-xzv4n","ts-gateway-service","ts-gateway-service-7f988fb8c4-b4d4j","ts-inside-payment-service","ts-inside-payment-service-5ccb8ccb87-vf4gb","ts-news-service","ts-news-service-6d6c6d7855-lp5kp","ts-notification-service","ts-notification-service-58f6c468d7-k475l","ts-order-other-service","ts-order-other-service-5d6878687f-wn5bw","ts-order-service","ts-order-service-6794d6f564-6gqxf","ts-payment-service","ts-payment-service-58854d694-pc5fc","ts-preserve-other-service","ts-preserve-other-service-64fd9c88cf-ft2vr","ts-preserve-service","ts-preserve-service-696df489d4-84dch","ts-price-service","ts-price-service-67c895b45-x5xx6","ts-rebook-service","ts-rebook-service-7c7644bbdd-9pn4q","ts-route-plan-service","ts-route-plan-service-556cddc5c9-7tcxt","ts-route-service","ts-route-service-cfc6dbcf7-2zh9m","ts-seat-service","ts-seat-service-6c78b7d797-dj98m","ts-security-service","ts-security-service-55f5b777bb-hljpr","ts-station-food-service","ts-station-food-service-746f6779d7-l25nh","ts-station-service","ts-station-service-65986cc944-95bp4","ts-ticket-office-service","ts-ticket-office-service-d7c58b8c7-bvrzr","ts-train-food-service","ts-train-food-service-d5485c677-cqkk8","ts-train-service","ts-train-service-9b56d75b6-4dmhb","ts-travel-plan-service","ts-travel-plan-service-7875c49896-tjpzq","ts-travel-service","ts-travel-service-c7b5c6d9b-g9ttj","ts-travel2-service","ts-travel2-service-7ff5bbbf54-rh6v6","ts-ui-dashboard","ts-ui-dashboard-57867cb85c-zzh8v","ts-user-service","ts-user-service-54dd6b48c-bp59d","ts-verification-code-service","ts-verification-code-service-85785c4f79-sf7x6","ts-voucher-service","ts-voucher-service-689c4fc885-j9pqj","ts-wait-order-service","ts-wait-order-service-7cf6bc9468-2lrck","worker1","worker2","worker3","worker4","worker5","worker6"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[3.745,11.236,18.727,26.218,33.709,41.2,48.691,56.182,63.673,71.164,78.654,86.145,93.636,101.127,108.618,116.109,123.6,131.091,138.582,146.073,153.563,161.054,168.545,176.036,183.527,191.018,198.509,206.0,213.491,220.982,228.472,235.963,243.454,250.945,258.436,265.927,273.418,280.909,288.4,295.89,303.381,310.872,318.363,325.854,333.345,340.836,348.327,355.818,363.309,370.799,378.29,385.781,393.272,400.763,408.254,415.745,423.236,430.727,438.218,445.708,453.199,460.69,468.181,475.672]
[M1] rank=1 service=ts-voucher-service metric=k8s.pod.memory.node.utilization baseline=0.000293 peak=0.000298 signed_z=999.0 onset_bin=0 onset_rel_s=3.745 persistence_bins=64
values_compact=rle:0.000293*55,0.000295*1,0.000298*8
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M2] rank=2 service=ts-consign-service metric=k8s.pod.memory.page_faults baseline=149581.083333 peak=163826.0 signed_z=38.383 onset_bin=39 onset_rel_s=295.89 persistence_bins=25
values_compact=delta:148645,0,399,0,0,159,0,242,87,0,40,0,70,0,0,34,0,8,8,0,0,12,0,42,41,0,33,0,305,0,21,0,174,0,0,198,91,35,35,77,77,49.5,49.5,74,74,486,486,11,11,0,643,19.5,19.5,10.5,10.5,34,0,4378,0,38,6576,0,0,23
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M3] rank=3 service=ts-consign-service metric=container.memory.page_faults baseline=148900.354167 peak=163153.0 signed_z=35.083 onset_bin=41 onset_rel_s=310.872 persistence_bins=23
values_compact=delta:147455,537,0,392,142,119.5,119.5,28,0,80,0,28,0,38.5,38.5,12,12,6,6,3,3,17,17,0,57,0,0,56,282,0,0,52,143,0,156,0,133,35,35,37,0,193,0,158,967,0,24,4.5,4.5,160,0,521,0,24,0,39,0,4377,0,39,0,6578,0,24
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M4] rank=4 service=ts-config-service metric=k8s.pod.memory.rss baseline=781811882.666667 peak=799354880.0 signed_z=34.624 onset_bin=50 onset_rel_s=378.29 persistence_bins=14
values_compact=delta:781578240,57344,57344,0,196608,0,-868352,0,0,0,0,94208,0,8192,0,827392,0,49152,0,69632,69632,40960,0,90112,0,0,36864,20480,20480,53248,53248,2048,2048,4096,0,425984,114688,0,0,-65536,0,0,0,0,0,8192,0,65536,65536,0,2445312,0,13549568,0,0,94208,0,8192,0,45056,0,131072,0,2048
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M5] rank=5 service=rabbitmq metric=container.memory.rss baseline=153521322.666667 peak=153677824.0 signed_z=33.111 onset_bin=61 onset_rel_s=460.69 persistence_bins=2
values_compact=rle:153518080*21,153522176*1,153526272*6,153530368*24,153534464*9,153606144*1,153677824*1,153534464*1
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M6] rank=6 service=ts-config-service metric=k8s.pod.memory.page_faults baseline=155438.145833 peak=170078.0 signed_z=32.429 onset_bin=50 onset_rel_s=378.29 persistence_bins=14
values_compact=delta:154522,23,23,0,104,0,623,0,37,0,0,46,0,20,0,220,0,47,0,26.5,26.5,42,0,41,11,0,26,11,11,21,21,13,13,12,0,142,41,0,0,24,14,0,18,0,0,22,0,32.5,32.5,0,4688,0,8966,0,0,46,0,18,0,23,0,52,0,9.5
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M7] rank=7 service=ts-config-service metric=container.memory.page_faults baseline=154634.645833 peak=169281.0 signed_z=30.501 onset_bin=50 onset_rel_s=378.29 persistence_bins=14
values_compact=delta:153096,682,0,44,72,0,577,0,71,0,15,0,46,0,0,225,0,38,0,38,61,8.5,8.5,18,18,0,30,0,27,0,45,9,9,10,10,138,0,25,25,0,22,9,9,0,23,0,18,0,95,0,4642,4478.5,4478.5,9.5,9.5,18,18,15.5,15.5,13,0,13,0,48
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M8] rank=8 service=ts-consign-service metric=k8s.pod.memory.rss baseline=752722005.333333 peak=786767872.0 signed_z=29.355 onset_bin=38 onset_rel_s=288.4 persistence_bins=26
values_compact=delta:749596672,0,1560576,0,0,385024,0,937984,184320,0,110592,0,221184,0,0,69632,0,0,0,0,0,4096,0,98304,118784,0,8192,0,1105920,0,16384,0,622592,0,0,643072,323584,110592,110592,280576,280576,157696,157696,280576,280576,149504,149504,-28672,-28672,0,2478080,49152,49152,8192,8192,102400,0,-802816,0,77824,26890240,0,0,-11853824
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M9] rank=9 service=ts-consign-service metric=k8s.pod.memory.node.utilization baseline=0.005662 peak=0.005914 signed_z=28.267 onset_bin=39 onset_rel_s=295.89 persistence_bins=25
values_compact=rle:0.005638*2,0.00565*3,0.005652*2,0.005659*1,0.005661*2,0.005671*2,0.005663*3,0.005664*8,0.005667*1,0.005665*4,0.005673*4,0.005678*3,0.005683*1,0.005685*1,0.005686*1,0.005687*1,0.005689*1,0.005691*1,0.005693*1,0.005694*1,0.005696*1,0.005698*1,0.005699*1,0.0057*1,0.005702*1,0.005704*2,0.005718*1,0.005719*4,0.00572*2,0.005717*2,0.005714*1,0.005914*3,0.005828*1
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M10] rank=10 service=ts-consign-service metric=k8s.pod.memory.usage baseline=764511829.333333 peak=798515200.0 signed_z=28.267 onset_bin=39 onset_rel_s=295.89 persistence_bins=25
values_compact=delta:761311232,0,1560576,0,0,356352,0,937984,188416,0,1413120,0,-1073152,0,0,65536,0,0,0,0,0,4096,0,413696,-167936,0,-16384,0,1077248,0,20480,0,622592,0,0,663552,323584,110592,110592,296960,296960,169984,169984,282624,282624,151552,151552,210944,210944,0,1974272,53248,53248,4096,4096,102400,0,-303104,0,-421888,26902528,0,0,-11599872
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M11] rank=11 service=ts-consign-service metric=k8s.pod.memory.working_set baseline=764126805.333333 peak=798130176.0 signed_z=28.267 onset_bin=39 onset_rel_s=295.89 persistence_bins=25
values_compact=delta:760926208,0,1560576,0,0,356352,0,937984,188416,0,1413120,0,-1073152,0,0,65536,0,0,0,0,0,4096,0,413696,-167936,0,-16384,0,1077248,0,20480,0,622592,0,0,663552,323584,110592,110592,296960,296960,169984,169984,282624,282624,151552,151552,210944,210944,0,1974272,53248,53248,4096,4096,102400,0,-303104,0,-421888,26902528,0,0,-11599872
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M12] rank=12 service=ts-consign-service metric=k8s.pod.memory.available baseline=2457098666.666667 peak=2423095296.0 signed_z=-28.267 onset_bin=39 onset_rel_s=295.89 persistence_bins=25
values_compact=delta:2460299264,0,-1560576,0,0,-356352,0,-937984,-188416,0,-1413120,0,1073152,0,0,-65536,0,0,0,0,0,-4096,0,-413696,167936,0,16384,0,-1077248,0,-20480,0,-622592,0,0,-663552,-323584,-110592,-110592,-296960,-296960,-169984,-169984,-282624,-282624,-151552,-151552,-210944,-210944,0,-1974272,-53248,-53248,-4096,-4096,-102400,0,303104,0,421888,-26902528,0,0,11599872
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[414.4134647846222,479.4175066947937]

=== LOG SUMMARY ===
{"entries":[{"error_logs":5000,"error_pct":19.35,"service":"ts-seat-service","total_logs":25844},{"error_logs":504,"error_pct":16.35,"service":"ts-food-service","total_logs":3082},{"error_logs":188,"error_pct":6.05,"service":"ts-preserve-service","total_logs":3108},{"error_logs":150,"error_pct":1.62,"service":"ts-order-service","total_logs":9253},{"error_logs":96,"error_pct":25.0,"service":"ts-notification-service","total_logs":384},{"error_logs":96,"error_pct":25.0,"service":"ts-delivery-service","total_logs":384},{"error_logs":50,"error_pct":0.39,"service":"ts-travel-service","total_logs":12724},{"error_logs":49,"error_pct":0.31,"service":"ts-basic-service","total_logs":15796}],"mode":"errors","omitted_services":22,"service_count":30}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":-49.8,"error_pct":0.51,"p95_during_ms":369.99825589999983,"p95_pre_ms":736.6197990499977,"service":"ts-route-plan-service","spans":2817},{"delta_pct":-45.5,"error_pct":1.41,"p95_during_ms":69.231656,"p95_pre_ms":127.02853944999997,"service":"ts-travel-service","spans":14055},{"delta_pct":-43.6,"error_pct":0.0,"p95_during_ms":11.6969734,"p95_pre_ms":20.754987049999965,"service":"ts-seat-service","spans":20634},{"delta_pct":-42.8,"error_pct":0.0,"p95_during_ms":6.034273899999985,"p95_pre_ms":10.556568799999997,"service":"ts-assurance-service","spans":1046},{"delta_pct":-41.1,"error_pct":0.4,"p95_during_ms":476.189821,"p95_pre_ms":808.5737038999998,"service":"ts-travel-plan-service","spans":3698},{"delta_pct":-38.9,"error_pct":0.0,"p95_during_ms":2.7557641,"p95_pre_ms":4.513668,"service":"ts-config-service","spans":25020},{"delta_pct":-37.5,"error_pct":0.0,"p95_during_ms":8.882163199999999,"p95_pre_ms":14.216194299999998,"service":"ts-consign-service","spans":1140},{"delta_pct":-36.7,"error_pct":0.0,"p95_during_ms":5.60370925,"p95_pre_ms":8.850666999999985,"service":"ts-contacts-service","spans":4913}],"omitted_services":22,"service_count":30}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=35 omitted_edges=0
[{"evidence_source":"metric","onset_rel_s":270.0,"rank":1,"service":"ts-payment-service","severity_z":12.115},{"evidence_source":"metric","onset_rel_s":313.2,"rank":2,"service":"ts-auth-service","severity_z":12.361},{"evidence_source":"metric","onset_rel_s":319.8,"rank":3,"service":"ts-route-plan-service","severity_z":14.263},{"evidence_source":"metric","onset_rel_s":322.8,"rank":4,"service":"ts-travel-plan-service","severity_z":11.049},{"evidence_source":"metric","onset_rel_s":372.6,"rank":5,"service":"ts-consign-price-service","severity_z":19.568},{"evidence_source":"metric","onset_rel_s":393.0,"rank":6,"service":"ts-config-service","severity_z":34.624},{"evidence_source":"metric","onset_rel_s":393.0,"rank":7,"service":"ts-route-service","severity_z":15.485},{"evidence_source":"metric","onset_rel_s":398.4,"rank":8,"service":"ts-preserve-service","severity_z":17.714},{"evidence_source":"metric","onset_rel_s":403.8,"rank":9,"service":"ts-avatar-service","severity_z":18.663},{"evidence_source":"metric","onset_rel_s":413.4,"rank":10,"service":"ts-security-service","severity_z":11.73},{"evidence_source":"metric","onset_rel_s":419.4,"rank":11,"service":"ts-voucher-service","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":427.8,"rank":12,"service":"ts-consign-service","severity_z":38.383},{"evidence_source":"trace","onset_rel_s":444.6,"rank":13,"service":"ts-station-food-service","severity_z":12.702},{"evidence_source":"metric","onset_rel_s":463.2,"rank":14,"service":"rabbitmq","severity_z":33.111}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"ts-consign-price-service","caller":"ts-consign-service"},{"callee":"ts-security-service","caller":"ts-preserve-service"},{"callee":"ts-route-service","caller":"ts-route-plan-service"},{"callee":"ts-route-plan-service","caller":"ts-travel-plan-service"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

[excluded before optimizer]

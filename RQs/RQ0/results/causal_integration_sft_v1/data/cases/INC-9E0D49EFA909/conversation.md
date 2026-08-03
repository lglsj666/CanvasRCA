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
opaque_id: INC-9E0D49EFA909
observation_window={"duration_rel_s":477.342,"source_metric_rows":1078}
selection_summary={"candidate_count":104,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":1018,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["loadgenerator","loadgenerator-877c5fc96-rf7tx","mysql","mysql-0","rabbitmq","rabbitmq-0","ts-admin-basic-info-service","ts-admin-basic-info-service-65df4c5d86-cwg6g","ts-admin-order-service","ts-admin-order-service-7bb4f698d7-s6wb7","ts-admin-route-service","ts-admin-route-service-5b9fcdbf98-h47nw","ts-admin-travel-service","ts-admin-travel-service-7ccb4f69cf-7sx7g","ts-admin-user-service","ts-admin-user-service-56c4b4dcbd-szhgx","ts-assurance-service","ts-assurance-service-5c77657bcb-xlpgq","ts-auth-service","ts-auth-service-cc77d6f9-9mjkt","ts-avatar-service","ts-avatar-service-5454b669ff-mvh7c","ts-basic-service","ts-basic-service-dffc5b899-zqpbb","ts-cancel-service","ts-cancel-service-697f84df75-ldmld","ts-config-service","ts-config-service-7b97b98795-pfbl2","ts-consign-price-service","ts-consign-price-service-75f975bd76-g9hbf","ts-consign-service","ts-consign-service-6857bf796d-9rvjd","ts-contacts-service","ts-contacts-service-bf469d8f6-59l2v","ts-delivery-service","ts-delivery-service-6f495f545-5grtj","ts-execute-service","ts-execute-service-65b69d766-ldr9r","ts-food-delivery-service","ts-food-delivery-service-777b64d578-v8hv2","ts-food-service","ts-food-service-59b5c65f89-sxch5","ts-gateway-service","ts-gateway-service-847b8c9767-259lx","ts-inside-payment-service","ts-inside-payment-service-75ffb88dbb-twttm","ts-news-service","ts-news-service-7869d45c45-2vwnk","ts-notification-service","ts-notification-service-78796d88d6-q5cx2","ts-order-other-service","ts-order-other-service-6477b6cd98-jvdxx","ts-order-service","ts-order-service-6f4cfb5df7-6frr6","ts-payment-service","ts-payment-service-64bdf8c88c-gb55s","ts-preserve-other-service","ts-preserve-other-service-8774fbf78-ngpfk","ts-preserve-service","ts-preserve-service-6f7ff8d889-zjl6l","ts-price-service","ts-price-service-6d8564b588-6w6qs","ts-rebook-service","ts-rebook-service-f996d677c-g7jcb","ts-route-plan-service","ts-route-plan-service-6d5c54cb74-5sn8p","ts-route-service","ts-route-service-c4496565b-24zp6","ts-seat-service","ts-seat-service-94b957996-whzwz","ts-security-service","ts-security-service-6d487fd867-d4m48","ts-station-food-service","ts-station-food-service-585dfddcfd-wplsl","ts-station-service","ts-station-service-76f56dcbf-6jhqv","ts-ticket-office-service","ts-ticket-office-service-778556c8b6-nlbd9","ts-train-food-service","ts-train-food-service-5975fbbccb-7mwms","ts-train-service","ts-train-service-56bbd9b4c5-m8w99","ts-travel-plan-service","ts-travel-plan-service-85b47db797-jjjtn","ts-travel-service","ts-travel-service-c588d796f-hghbn","ts-travel2-service","ts-travel2-service-7565f66f4c-nbplg","ts-ui-dashboard","ts-ui-dashboard-78c8f55d5d-lh7br","ts-user-service","ts-user-service-6f674f6cc8-k5f95","ts-verification-code-service","ts-verification-code-service-544d85fbb6-l5jzp","ts-voucher-service","ts-voucher-service-75f4db5b54-cqng7","ts-wait-order-service","ts-wait-order-service-568568585c-4xvkg","worker1","worker2","worker3","worker4","worker5","worker6"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[3.729,11.188,18.646,26.105,33.563,41.022,48.48,55.939,63.397,70.855,78.314,85.772,93.231,100.689,108.148,115.606,123.065,130.523,137.982,145.44,152.899,160.357,167.816,175.274,182.733,190.191,197.65,205.108,212.566,220.025,227.483,234.942,242.4,249.859,257.317,264.776,272.234,279.693,287.151,294.61,302.068,309.527,316.985,324.444,331.902,339.36,346.819,354.277,361.736,369.194,376.653,384.111,391.57,399.028,406.487,413.945,421.404,428.862,436.321,443.779,451.238,458.696,466.155,473.613]
[M1] rank=1 service=ts-travel-service metric=hubble_http_request_duration_p90_seconds baseline=0.114197 peak=5.08 signed_z=385.127 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.117386,-0.018973,-0.005048,0.015385,0.008696,0.006087,-0.005244,0.018104,1.828607,2.930625,-0.118125,0.2525,-0.5,0.49875,0.05125,-4.95
missing_mask_bits=0111011101110111011101110111011101110111011101110111011101110111
observed_counts_compact=csv:1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0
[M2] rank=2 service=ts-travel-service metric=hubble_http_request_duration_p50_seconds baseline=0.035508 peak=5.025 signed_z=311.043 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.034375,-0.006875,-0.006424,0.00336,0.001345,0.004631,0.01721,0.025235,-0.025982,-0.024375,3.111875,-3.103125,0.010417,-0.010417,0.01125,4.9825
missing_mask_bits=1011101110111011101110111011101110111011101110111011101110111011
observed_counts_compact=csv:0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0
[M3] rank=3 service=ts-ui-dashboard metric=hubble_http_request_duration_p95_seconds baseline=0.026967 peak=10.0 signed_z=292.131 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.009737,-0.000006,0.105269,-0.0825,-0.022844,0.000034,-0.000017,0.010077,-0.01025,2.745375,-2.611854,-0.028146,0.000125,8.885,1
missing_mask_bits=1101110111011101110111011101110111111101110111011101110111011101
observed_counts_compact=rle:0*2,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*7,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*1
[M4] rank=4 service=ts-route-plan-service metric=hubble_http_request_duration_p90_seconds baseline=0.164073 peak=10.0 signed_z=141.098 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.283333,-0.189583,0.08125,-0.025,0.049,-0.1215,0.0165,0.146,5.76,-5.935,8.935,0,1
missing_mask_bits=0111011101110111011101110111011101110111011111110111011111111111
observed_counts_compact=rle:1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*7,1*1,0*3,1*1,0*11
[M5] rank=5 service=ts-price-service metric=hubble_http_request_duration_p90_seconds baseline=0.007232 peak=0.425 signed_z=85.04 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.007417,-0.002767,0.000247,0.000853,-0.00125,0.000141,0.001359,0.014,-0.0105,-0.005,0.003,0.02,-0.018,-0.005,0.043,0.3775
missing_mask_bits=1101110111011101110111011101110111011101110111011101110111011101
observed_counts_compact=csv:0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0
[M6] rank=6 service=ts-price-service metric=hubble_http_request_duration_p95_seconds baseline=0.008689 peak=0.4625 signed_z=83.426 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.008708,-0.0038,0.002967,0,-0.003125,0.000148,0.003102,0.0145,-0.01275,-0.005,0.004,0.03,-0.029,-0.005,0.044,0.41375
missing_mask_bits=1101110111011101110111011101110111011101110111011101110111011101
observed_counts_compact=csv:0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0
[M7] rank=7 service=ts-route-plan-service metric=hubble_http_request_duration_p95_seconds baseline=0.268115 peak=10.0 signed_z=80.908 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.391667,-0.254167,0.175,-0.1125,0.0395,-0.15075,0.21125,0.175,7.525,-7.9175,9.4175,0,0.5
missing_mask_bits=0111011101110111011101110111011101110111011111110111011111111111
observed_counts_compact=rle:1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*7,1*1,0*3,1*1,0*11
[M8] rank=8 service=loadgenerator metric=hubble_http_request_duration_p95_seconds baseline=0.244397 peak=10.0 signed_z=80.563 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.284375,-0.115,-0.071319,0.189444,-0.0705,-0.048964,0.037797,0.319167,1.075,-1.3125,9.7125,0,-0.25,-1
missing_mask_bits=0111011101110111011101110111011101110111111101110111011101111111
observed_counts_compact=rle:1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*7,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*7
[M9] rank=9 service=loadgenerator metric=hubble_http_request_duration_p90_seconds baseline=0.149804 peak=10.0 signed_z=79.17 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.092935,0.003136,-0.00991,0.033251,-0.031376,0.005475,0.053797,0.327692,5.025,4.25,-9.533333,-0.046667,-0.072,0.802,9.1
missing_mask_bits=1101110111011101110111011101110111111101110111011101110111011101
observed_counts_compact=rle:0*2,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*7,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*1
[M10] rank=10 service=ts-ui-dashboard metric=hubble_http_request_duration_p99_seconds baseline=0.057448 peak=10.0 signed_z=79.102 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.00995,-0.000006,-0.000005,-0.000016,0.000005,0.380072,-0.38005,0,1.087525,2.6325,6.270025,-4.995025,-4.995025,0.0378,-0.0378
missing_mask_bits=1011101110111011101110111011101110111011101110111011101110111111
observed_counts_compact=rle:0*1,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*6
[M11] rank=11 service=ts-price-service metric=hubble_http_request_duration_p50_seconds baseline=0.003011 peak=0.03125 signed_z=76.212 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.003304,-0.000069,-0.000497,-0.000011,-0.00001,-0.000124,0.000428,0.000729,0.0025,-0.00375,0,0.0025,-0.001667,-0.000476,0.028393
missing_mask_bits=1011101110111011101110111011101110111011101110111011101110111111
observed_counts_compact=rle:0*1,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*6
[M12] rank=12 service=ts-route-plan-service metric=hubble_http_request_duration_p99_seconds baseline=0.506292 peak=10.0 signed_z=58.265 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.46625,-0.01125,-0.04,0.06125,0.25875,-0.4955,0.5405,-0.296667,9.516667,-9.7515,-0.19875,-0.00075,9.951,0
missing_mask_bits=1110111011101110111011101110111011101110111011101111111011101111
observed_counts_compact=rle:0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*7,1*1,0*3,1*1,0*4

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[210.94577550888062,450.9457755088806]

=== LOG SUMMARY ===
{"entries":[{"error_logs":6387,"error_pct":100.0,"service":"ts-ui-dashboard","total_logs":6387},{"error_logs":316,"error_pct":17.32,"service":"ts-food-service","total_logs":1825},{"error_logs":72,"error_pct":1.4,"service":"ts-order-service","total_logs":5161},{"error_logs":72,"error_pct":4.05,"service":"ts-preserve-service","total_logs":1776},{"error_logs":67,"error_pct":25.87,"service":"ts-notification-service","total_logs":259},{"error_logs":66,"error_pct":25.19,"service":"ts-delivery-service","total_logs":262},{"error_logs":2,"error_pct":0.03,"service":"ts-travel-service","total_logs":6755}],"mode":"errors","omitted_services":24,"service_count":31}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":4634.6,"error_pct":0.48,"p95_during_ms":6163.8477099,"p95_pre_ms":130.18741025,"service":"ts-travel-service","spans":7344},{"delta_pct":3627.4,"error_pct":0.0,"p95_during_ms":18668.8984422,"p95_pre_ms":500.8506929,"service":"ts-route-plan-service","spans":1463},{"delta_pct":2855.2,"error_pct":0.0,"p95_during_ms":18834.706115599998,"p95_pre_ms":637.3441825999994,"service":"ts-travel-plan-service","spans":1986},{"delta_pct":459.8,"error_pct":0.0,"p95_during_ms":1148.451815149998,"p95_pre_ms":205.144982,"service":"ts-ui-dashboard","spans":6385},{"delta_pct":452.7,"error_pct":0.11,"p95_during_ms":1154.6194699499995,"p95_pre_ms":208.91265584999985,"service":"loadgenerator","spans":6386},{"delta_pct":424.3,"error_pct":0.0,"p95_during_ms":7313.408211500001,"p95_pre_ms":1394.8137949,"service":"ts-preserve-service","spans":1132},{"delta_pct":188.1,"error_pct":0.0,"p95_during_ms":50.29205229999999,"p95_pre_ms":17.456913850000003,"service":"ts-seat-service","spans":11493},{"delta_pct":175.4,"error_pct":0.0,"p95_during_ms":10.736709149999996,"p95_pre_ms":3.8981326499999973,"service":"ts-price-service","spans":3810}],"omitted_services":22,"service_count":30}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=35 omitted_edges=13
[{"evidence_source":"trace","onset_rel_s":213.6,"rank":1,"service":"ts-ui-dashboard","severity_z":125.938},{"evidence_source":"trace","onset_rel_s":213.6,"rank":2,"service":"ts-config-service","severity_z":166.316},{"evidence_source":"trace","onset_rel_s":213.6,"rank":3,"service":"ts-route-plan-service","severity_z":164.528},{"evidence_source":"trace","onset_rel_s":213.6,"rank":4,"service":"ts-travel-plan-service","severity_z":139.435},{"evidence_source":"trace","onset_rel_s":213.6,"rank":5,"service":"loadgenerator","severity_z":127.512},{"evidence_source":"trace","onset_rel_s":213.6,"rank":6,"service":"ts-travel2-service","severity_z":97.989},{"evidence_source":"trace","onset_rel_s":213.6,"rank":7,"service":"ts-basic-service","severity_z":91.02},{"evidence_source":"trace","onset_rel_s":213.6,"rank":8,"service":"ts-seat-service","severity_z":67.775},{"evidence_source":"trace","onset_rel_s":213.6,"rank":9,"service":"ts-route-service","severity_z":52.431},{"evidence_source":"trace","onset_rel_s":223.8,"rank":10,"service":"ts-price-service","severity_z":779.996},{"evidence_source":"trace","onset_rel_s":233.4,"rank":11,"service":"ts-travel-service","severity_z":517.416},{"evidence_source":"trace","onset_rel_s":233.4,"rank":12,"service":"ts-station-service","severity_z":75.304},{"evidence_source":"trace","onset_rel_s":333.0,"rank":13,"service":"ts-order-service","severity_z":128.704},{"evidence_source":"trace","onset_rel_s":412.8,"rank":14,"service":"ts-order-other-service","severity_z":159.879}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"ts-ui-dashboard","caller":"loadgenerator"},{"callee":"ts-price-service","caller":"ts-basic-service"},{"callee":"ts-route-service","caller":"ts-basic-service"},{"callee":"ts-station-service","caller":"ts-basic-service"},{"callee":"ts-route-service","caller":"ts-route-plan-service"},{"callee":"ts-travel-service","caller":"ts-route-plan-service"},{"callee":"ts-travel2-service","caller":"ts-route-plan-service"},{"callee":"ts-config-service","caller":"ts-seat-service"},{"callee":"ts-order-other-service","caller":"ts-seat-service"},{"callee":"ts-order-service","caller":"ts-seat-service"},{"callee":"ts-route-plan-service","caller":"ts-travel-plan-service"},{"callee":"ts-seat-service","caller":"ts-travel-plan-service"},{"callee":"ts-basic-service","caller":"ts-travel-service"},{"callee":"ts-route-service","caller":"ts-travel-service"},{"callee":"ts-seat-service","caller":"ts-travel-service"},{"callee":"ts-basic-service","caller":"ts-travel2-service"},{"callee":"ts-route-service","caller":"ts-travel2-service"},{"callee":"ts-seat-service","caller":"ts-travel2-service"},{"callee":"ts-order-other-service","caller":"ts-ui-dashboard"},{"callee":"ts-order-service","caller":"ts-ui-dashboard"},{"callee":"ts-route-service","caller":"ts-ui-dashboard"},{"callee":"ts-travel-plan-service","caller":"ts-ui-dashboard"},{"callee":"ts-travel-service","caller":"ts-ui-dashboard"},{"callee":"ts-travel2-service","caller":"ts-ui-dashboard"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

[excluded before optimizer]

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
opaque_id: INC-5A062D6CB6CF
observation_window={"duration_rel_s":479.511,"source_metric_rows":1080}
selection_summary={"candidate_count":104,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":1023,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["loadgenerator","loadgenerator-794b57d884-5z9x5","mysql","mysql-0","rabbitmq","rabbitmq-0","ts-admin-basic-info-service","ts-admin-basic-info-service-8489f5b9dd-svfj9","ts-admin-order-service","ts-admin-order-service-5b6c548fb5-cj95l","ts-admin-route-service","ts-admin-route-service-6b7fcc6f9b-x64xj","ts-admin-travel-service","ts-admin-travel-service-7d4bb8dcb9-m5cnp","ts-admin-user-service","ts-admin-user-service-5bff4bdf86-dplnn","ts-assurance-service","ts-assurance-service-5597965598-lbqrc","ts-auth-service","ts-auth-service-6d87cc4dc7-484mw","ts-avatar-service","ts-avatar-service-7c465d78b5-7mbjf","ts-basic-service","ts-basic-service-6968d4ccd5-7n2bb","ts-cancel-service","ts-cancel-service-6cf95f89fc-n7qxc","ts-config-service","ts-config-service-5d4b464d85-jbwjs","ts-consign-price-service","ts-consign-price-service-7d59bdd47d-r2xf6","ts-consign-service","ts-consign-service-848b6d5bcd-f4tx2","ts-contacts-service","ts-contacts-service-55cfbdfdc8-pw5zn","ts-delivery-service","ts-delivery-service-d66597c7f-cm9ct","ts-execute-service","ts-execute-service-6687b7f74d-t4rcs","ts-food-delivery-service","ts-food-delivery-service-bcb844d44-gfqqf","ts-food-service","ts-food-service-55f49f6b59-f9zjs","ts-gateway-service","ts-gateway-service-7cc7b478fc-mj4mc","ts-inside-payment-service","ts-inside-payment-service-6d88d7f6b4-qkxv5","ts-news-service","ts-news-service-6d6c6d7855-6fhb8","ts-notification-service","ts-notification-service-596b87f8f6-vvvc4","ts-order-other-service","ts-order-other-service-5fc6774cd8-6hdjm","ts-order-service","ts-order-service-668587b48c-w6wb8","ts-payment-service","ts-payment-service-7679c6959c-mcsq8","ts-preserve-other-service","ts-preserve-other-service-6bf648d676-stq2x","ts-preserve-service","ts-preserve-service-5d979f4b55-cln6r","ts-price-service","ts-price-service-55957b666-txpm4","ts-rebook-service","ts-rebook-service-79d845d787-4sfjs","ts-route-plan-service","ts-route-plan-service-6865bfcc6d-wm2c4","ts-route-service","ts-route-service-586ffc746-pxxqx","ts-seat-service","ts-seat-service-7b7c5f5d7d-k6qmp","ts-security-service","ts-security-service-5454c847f7-vwq8k","ts-station-food-service","ts-station-food-service-cb9656f7b-tjxgq","ts-station-service","ts-station-service-685fd4985f-4h7cq","ts-ticket-office-service","ts-ticket-office-service-9c7b9d55b-kgdxg","ts-train-food-service","ts-train-food-service-bdd545d98-j9rzj","ts-train-service","ts-train-service-7b96f444bf-xqg5t","ts-travel-plan-service","ts-travel-plan-service-b49559b55-77dts","ts-travel-service","ts-travel-service-56c9999f79-tjbqf","ts-travel2-service","ts-travel2-service-8557fd66df-8d58h","ts-ui-dashboard","ts-ui-dashboard-68fff76764-ztk6r","ts-user-service","ts-user-service-644dc6f8fb-bbn8v","ts-verification-code-service","ts-verification-code-service-595bc8dd8d-n6w48","ts-voucher-service","ts-voucher-service-c745bfccb-dgrdt","ts-wait-order-service","ts-wait-order-service-779f77459-txsdh","worker1","worker2","worker3","worker4","worker5","worker6"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[3.746,11.239,18.731,26.223,33.716,41.208,48.7,56.193,63.685,71.177,78.67,86.162,93.654,101.147,108.639,116.131,123.624,131.116,138.609,146.101,153.593,161.086,168.578,176.07,183.563,191.055,198.547,206.04,213.532,221.024,228.517,236.009,243.501,250.994,258.486,265.978,273.471,280.963,288.456,295.948,303.44,310.933,318.425,325.917,333.41,340.902,348.394,355.887,363.379,370.871,378.364,385.856,393.348,400.841,408.333,415.826,423.318,430.81,438.303,445.795,453.287,460.78,468.272,475.764]
[M1] rank=1 service=ts-basic-service metric=hubble_http_request_duration_p95_seconds baseline=0.009589 peak=0.115 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.009801,-0.000154,-0.000099,-0.000124,0.00017,0.000048,-0.000106,-0.000018,-0.000075,0.000322,-0.000171,0.000031,0.000125,0.06775,0.0175,0.02
missing_mask_bits=1110111011101110111011101110111011101110111011101110111011101110
observed_counts_compact=csv:0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1
[M2] rank=2 service=ts-order-service metric=hubble_http_request_duration_p90_seconds baseline=0.007415 peak=1.75 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.0083,-0.000447,-0.000486,-0.00043,0.000499,-0.000264,0.000087,-0.000266,-0.000355,-0.001138,0.001428,-0.000303,1.743375,-1.7195,-0.00925,-0.011528
missing_mask_bits=1110111011101110111011101110111011101110111011101110111011101110
observed_counts_compact=csv:0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1
[M3] rank=3 service=ts-station-service metric=hubble_http_request_duration_p90_seconds baseline=0.005587 peak=4.25 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.008233,-0.00265,-0.0005,-0.000139,0.00003,-0.000408,0.002101,-0.002024,0.000039,0.002818,-0.003,0.0043,-0.0043,0.0115,4.234,-4.20875
missing_mask_bits=1011101110111011101110111011101110111011101110111011101110111011
observed_counts_compact=csv:0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0
[M4] rank=4 service=ts-train-service metric=hubble_http_request_duration_p90_seconds baseline=0.006203 peak=3.5 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.007486,-0.000846,-0.00037,-0.000478,0.00045,-0.000492,0.000993,-0.002041,-0.000061,0.000859,-0.000839,0.002214,0,0.060625,-0.023125,3.455625
missing_mask_bits=1110111011101110111011101110111011101110111011101110111011101110
observed_counts_compact=csv:0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1
[M5] rank=5 service=ts-train-service metric=hubble_http_request_duration_p95_seconds baseline=0.007025 peak=4.25 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.008726,-0.001625,-0.000189,-0.000266,0.000256,-0.000277,0.000806,-0.001575,-0.000606,0.00125,-0.001,0.001687,0,0.099063,-0.046563,4.190313
missing_mask_bits=1110111011101110111011101110111011101110111011101110111011101110
observed_counts_compact=csv:0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1
[M6] rank=6 service=ts-voucher-service metric=k8s.pod.memory.node.utilization baseline=0.000308 peak=0.000308 signed_z=999.0 onset_bin=0 onset_rel_s=3.746 persistence_bins=64
values_compact=rle:0.000308*64
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,2,1,2,1,2,1
[M7] rank=7 service=ts-train-food-service metric=hubble_http_request_duration_p90_seconds baseline=0.009141 peak=0.35 signed_z=970.637 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.009545,-0.000264,0.000438,-0.000569,-0.000039,-0.000222,-0.000032,-0.000286,-0.001071,-0.0005,0.002333,0.340667,-0.31,0.0025,-0.022,0.0195
missing_mask_bits=1110111011101110111011101110111011101110111011101110111011101110
observed_counts_compact=csv:0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1
[M8] rank=8 service=ts-food-service metric=hubble_http_request_duration_p99_seconds baseline=0.023676 peak=0.4375 signed_z=873.634 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.02425,-0.00105,0.00117,-0.00132,0.00065,-0.0005,0.00084,-0.00044,0.4139,-0.42757,0.01417,-0.014167,0.014617,-0.0003,0.07475,0
missing_mask_bits=0111011101110111011101110111011101110111011101110111011101110111
observed_counts_compact=csv:1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0
[M9] rank=9 service=ts-verification-code-service metric=hubble_http_request_duration_p95_seconds baseline=0.00477 peak=0.027375 signed_z=847.374 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.00475,0,0.000059,-0.000059,0,0,0.000047,0.000011,-0.000058,0,0.00075,-0.00075,0,0.01625,0.006375,-0.02125
missing_mask_bits=1110111011101110111011101110111011101110111011101110111011101110
observed_counts_compact=csv:0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1
[M10] rank=10 service=loadgenerator metric=hubble_http_request_duration_p50_seconds baseline=0.009352 peak=0.076667 signed_z=809.574 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.009419,-0.000033,0.000008,-0.000049,0.000121,-0.000132,-0.00004,-0.000118,0.00061,0.000214,-0.000429,0.001311,-0.000507,0.01006,0.056232,-0.011667
missing_mask_bits=0111011101110111011101110111011101110111011101110111011101110111
observed_counts_compact=csv:1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0
[M11] rank=11 service=ts-train-food-service metric=hubble_http_request_duration_p99_seconds baseline=0.00989 peak=0.049625 signed_z=673.705 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.00995,-0.00004,0.00001,-0.00001,-0.000016,0.000038,-0.000076,-0.000106,0.00006,0.000123,-0.004983,0,0.00495,0.000033,0.039692,-0.024775
missing_mask_bits=0111011101110111011101110111011101110111011101110111011101110111
observed_counts_compact=csv:1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0
[M12] rank=12 service=ts-config-service metric=hubble_http_request_duration_p95_seconds baseline=0.004806 peak=0.040312 signed_z=673.003 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.004903,-0.000071,-0.000046,-0.000036,0.000082,0.000015,-0.000097,0,0.00017,-0.00017,0,0,0,0.035562,-0.018312,0.0025
missing_mask_bits=1110111011101110111011101110111011101110111011101110111011101110
observed_counts_compact=csv:0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[387.07726860046387,477.07726860046387]

=== LOG SUMMARY ===
{"entries":[{"error_logs":9041,"error_pct":100.0,"service":"ts-ui-dashboard","total_logs":9041},{"error_logs":436,"error_pct":17.24,"service":"ts-food-service","total_logs":2529},{"error_logs":119,"error_pct":4.99,"service":"ts-preserve-service","total_logs":2383},{"error_logs":119,"error_pct":1.73,"service":"ts-order-service","total_logs":6866},{"error_logs":96,"error_pct":25.0,"service":"ts-delivery-service","total_logs":384},{"error_logs":95,"error_pct":25.0,"service":"ts-notification-service","total_logs":380},{"error_logs":2,"error_pct":1.8,"service":"ts-inside-payment-service","total_logs":111},{"error_logs":1,"error_pct":1.92,"service":"ts-payment-service","total_logs":52}],"mode":"errors","omitted_services":23,"service_count":31}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":1197.5,"error_pct":0.0,"p95_during_ms":3575.9961529999996,"p95_pre_ms":275.61240779999997,"service":"ts-preserve-service","spans":1535},{"delta_pct":780.6,"error_pct":0.0,"p95_during_ms":4942.352424499997,"p95_pre_ms":561.2548371,"service":"ts-travel-plan-service","spans":2538},{"delta_pct":736.8,"error_pct":0.0,"p95_during_ms":33.4638455,"p95_pre_ms":3.999112199999999,"service":"ts-train-service","spans":12023},{"delta_pct":734.3,"error_pct":0.0,"p95_during_ms":776.3166713499945,"p95_pre_ms":93.04974859999996,"service":"ts-travel2-service","spans":6288},{"delta_pct":717.0,"error_pct":0.0,"p95_during_ms":3351.53404545,"p95_pre_ms":410.2110670999998,"service":"ts-route-plan-service","spans":1895},{"delta_pct":709.6,"error_pct":0.0,"p95_during_ms":291.474245,"p95_pre_ms":36.0006107,"service":"ts-basic-service","spans":8108},{"delta_pct":549.9,"error_pct":0.0,"p95_during_ms":25.824186999999988,"p95_pre_ms":3.973426000000001,"service":"ts-price-service","spans":5210},{"delta_pct":549.2,"error_pct":0.0,"p95_during_ms":25.233569599999974,"p95_pre_ms":3.8865869999999996,"service":"ts-station-service","spans":9130}],"omitted_services":22,"service_count":30}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=35 omitted_edges=2
[{"evidence_source":"metric","onset_rel_s":243.0,"rank":1,"service":"ts-food-service","severity_z":873.634},{"evidence_source":"trace","onset_rel_s":394.8,"rank":2,"service":"ts-station-service","severity_z":999.0},{"evidence_source":"trace","onset_rel_s":394.8,"rank":3,"service":"ts-train-service","severity_z":999.0},{"evidence_source":"trace","onset_rel_s":394.8,"rank":4,"service":"ts-route-service","severity_z":29.261},{"evidence_source":"trace","onset_rel_s":394.8,"rank":5,"service":"ts-ui-dashboard","severity_z":25.797},{"evidence_source":"trace","onset_rel_s":404.4,"rank":6,"service":"ts-basic-service","severity_z":115.438},{"evidence_source":"trace","onset_rel_s":404.4,"rank":7,"service":"ts-train-food-service","severity_z":19.042},{"evidence_source":"trace","onset_rel_s":404.4,"rank":8,"service":"ts-verification-code-service","severity_z":20.822},{"evidence_source":"trace","onset_rel_s":404.4,"rank":9,"service":"ts-config-service","severity_z":70.87},{"evidence_source":"trace","onset_rel_s":434.4,"rank":10,"service":"loadgenerator","severity_z":18.173},{"evidence_source":"metric","onset_rel_s":436.8,"rank":11,"service":"ts-voucher-service","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":447.0,"rank":12,"service":"ts-security-service","severity_z":261.156},{"evidence_source":"trace","onset_rel_s":454.8,"rank":13,"service":"ts-order-service","severity_z":59.367},{"evidence_source":"trace","onset_rel_s":464.4,"rank":14,"service":"ts-travel2-service","severity_z":31.052}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"ts-ui-dashboard","caller":"loadgenerator"},{"callee":"ts-route-service","caller":"ts-basic-service"},{"callee":"ts-station-service","caller":"ts-basic-service"},{"callee":"ts-train-service","caller":"ts-basic-service"},{"callee":"ts-train-food-service","caller":"ts-food-service"},{"callee":"ts-order-service","caller":"ts-security-service"},{"callee":"ts-basic-service","caller":"ts-travel2-service"},{"callee":"ts-route-service","caller":"ts-travel2-service"},{"callee":"ts-food-service","caller":"ts-ui-dashboard"},{"callee":"ts-order-service","caller":"ts-ui-dashboard"},{"callee":"ts-route-service","caller":"ts-ui-dashboard"},{"callee":"ts-train-service","caller":"ts-ui-dashboard"},{"callee":"ts-travel2-service","caller":"ts-ui-dashboard"},{"callee":"ts-verification-code-service","caller":"ts-ui-dashboard"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

[excluded before optimizer]

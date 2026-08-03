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
opaque_id: INC-FC632FFD701E
observation_window={"duration_rel_s":478.851,"source_metric_rows":1053}
selection_summary={"candidate_count":104,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":1016,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["loadgenerator","loadgenerator-b4559448f-mkgcf","mysql","mysql-0","rabbitmq","rabbitmq-0","ts-admin-basic-info-service","ts-admin-basic-info-service-85cc54c97c-hshg9","ts-admin-order-service","ts-admin-order-service-5dc6d7df84-j8q2n","ts-admin-route-service","ts-admin-route-service-67f847dfcc-jw99g","ts-admin-travel-service","ts-admin-travel-service-8446f69bdd-88tsd","ts-admin-user-service","ts-admin-user-service-6b4d5494c-zsb82","ts-assurance-service","ts-assurance-service-5775844f55-89xt7","ts-auth-service","ts-auth-service-6f5b7d4d64-lxl42","ts-avatar-service","ts-avatar-service-8684d88474-qzgfv","ts-basic-service","ts-basic-service-6d969cd7bd-np9bj","ts-cancel-service","ts-cancel-service-7566fb95d8-s7f9g","ts-config-service","ts-config-service-78cd5b655b-p8n8c","ts-consign-price-service","ts-consign-price-service-775fc46c9-fzd5z","ts-consign-service","ts-consign-service-77655cfd95-9llgq","ts-contacts-service","ts-contacts-service-7c44d4fc9f-kk22x","ts-delivery-service","ts-delivery-service-66b48565c8-9pb24","ts-execute-service","ts-execute-service-6b8d478797-484g5","ts-food-delivery-service","ts-food-delivery-service-df865c857-z5rwk","ts-food-service","ts-food-service-868676c6f4-pckjg","ts-gateway-service","ts-gateway-service-59bcdc5b64-xhvrf","ts-inside-payment-service","ts-inside-payment-service-6d497c8fcc-599rq","ts-news-service","ts-news-service-6d6c6d7855-69cmh","ts-notification-service","ts-notification-service-858f6b9957-th8mf","ts-order-other-service","ts-order-other-service-65f458c7fc-xb2vv","ts-order-service","ts-order-service-687867685d-fxg28","ts-payment-service","ts-payment-service-79b78f9c88-5kmdg","ts-preserve-other-service","ts-preserve-other-service-59ddb7699c-lstdm","ts-preserve-service","ts-preserve-service-b649b6578-s22gd","ts-price-service","ts-price-service-6b784db86c-5v4lx","ts-rebook-service","ts-rebook-service-5c7cd6f5cd-5g79t","ts-route-plan-service","ts-route-plan-service-64f7f6c585-lfjvz","ts-route-service","ts-route-service-5cdfd57bd7-f7drg","ts-seat-service","ts-seat-service-5c44567799-952f5","ts-security-service","ts-security-service-74fffc9d56-msnjb","ts-station-food-service","ts-station-food-service-7f6949d5df-65sz6","ts-station-service","ts-station-service-7b75998cfd-v2bxp","ts-ticket-office-service","ts-ticket-office-service-6bf44d54b7-bzkql","ts-train-food-service","ts-train-food-service-764c49649f-v2dn5","ts-train-service","ts-train-service-7fd4bc4b9b-85clw","ts-travel-plan-service","ts-travel-plan-service-69865d84f8-rr2gg","ts-travel-service","ts-travel-service-fbbd88b6b-rvnjn","ts-travel2-service","ts-travel2-service-7fd6cf5784-9hczp","ts-ui-dashboard","ts-ui-dashboard-cdd95b86c-5gptf","ts-user-service","ts-user-service-5b5b45f5b9-kq6tv","ts-verification-code-service","ts-verification-code-service-5cf9cc49d5-c4mw2","ts-voucher-service","ts-voucher-service-cddcc88c5-96sk6","ts-wait-order-service","ts-wait-order-service-7888ddf9cd-7kl4f","worker1","worker2","worker3","worker4","worker5","worker6"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[3.741,11.223,18.705,26.187,33.669,41.151,48.633,56.115,63.597,71.079,78.562,86.044,93.526,101.008,108.49,115.972,123.454,130.936,138.418,145.9,153.382,160.864,168.346,175.828,183.31,190.792,198.274,205.756,213.238,220.721,228.203,235.685,243.167,250.649,258.131,265.613,273.095,280.577,288.059,295.541,303.023,310.505,317.987,325.469,332.951,340.433,347.915,355.397,362.879,370.362,377.844,385.326,392.808,400.29,407.772,415.254,422.736,430.218,437.7,445.182,452.664,460.146,467.628,475.11]
[M1] rank=1 service=ts-basic-service metric=hubble_http_request_duration_p50_seconds baseline=0.003119 peak=5.00125 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.004083,-0.001011,0.000347,-0.000353,-0.000103,-0.0001,-0.000158,0.000073,0.000555,4.997917,0,0,-4.99875
missing_mask_bits=1011101110111011101110111011101110111111101111111011111110111011
observed_counts_compact=rle:0*1,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*7,1*1,0*7,1*1,0*7,1*1,0*3,1*1,0*2
[M2] rank=2 service=ts-basic-service metric=hubble_http_request_duration_p90_seconds baseline=0.006451 peak=10.0 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.006764,-0.000185,-0.000019,-0.000084,-0.000038,0.000112,-0.000536,0.000212,4.996024,4.99775,-9.9955,9.9955
missing_mask_bits=1101110111011101110111011101110111111101111111011111110111111101
observed_counts_compact=rle:0*2,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*7,1*1,0*7,1*1,0*7,1*1,0*7,1*1,0*1
[M3] rank=3 service=ts-basic-service metric=hubble_http_request_duration_p99_seconds baseline=0.007769 peak=5.002475 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.007432,-0.000037,0.003155,-0.003155,-0.000012,-0.000019,-0.000066,0.000039,4.745138,0.25,0,0,-4.997525
missing_mask_bits=1011101110111011101110111011101110111111101111111011111110111011
observed_counts_compact=rle:0*1,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*7,1*1,0*7,1*1,0*7,1*1,0*3,1*1,0*2
[M4] rank=4 service=ts-food-delivery-service metric=container.cpu.usage baseline=0.004566 peak=0.726234 signed_z=999.0 onset_bin=38 onset_rel_s=288.059 persistence_bins=7
values_compact=delta:0.004371,-0.00005,0,-0.000053,0,-0.000179,0.000776,0.000776,-0.000718,-0.000717,0.000034,0.000033,0.000149,0.000148,0.000557,0.000556,0,-0.001354,-0.000069,-0.00007,0,0.000689,-0.000402,-0.000401,0,0.000742,0,0,-0.000492,0,0.000494,0,-0.000502,0,-0.000026,-0.000025,0.000197,0.000196,0.360787,0.360787,-0.360782,-0.360783,-0.000528,-0.000527,0.000116,0.000116,0.001175,0.001175,0,-0.001024,0,0.001116,0,-0.000983,0,0.000465,0,-0.001512,0,-0.00008,0,0,0.001265,-0.00067
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1
[M5] rank=5 service=ts-food-delivery-service metric=k8s.pod.cpu.node.utilization baseline=3.7e-05 peak=0.005068 signed_z=999.0 onset_bin=38 onset_rel_s=288.059 persistence_bins=7
values_compact=rle:0.000043*2,0.000034*1,0.000033*2,0.000041*3,0.000033*1,0.000034*3,0.000035*2,0.000045*1,0.000038*3,0.000033*4,0.00004*1,0.000034*2,0.000039*2,0.000035*2,0.000037*3,0.000033*4,0.000036*2,0.002552*1,0.005068*1,0.000035*2,0.000033*1,0.00003*1,0.000031*1,0.000048*1,0.000042*1,0.000037*2,0.00004*3,0.000047*1,0.000053*1,0.00005*1,0.000047*1,0.000041*1,0.000035*2,0.000032*3,0.000042*2
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1
[M6] rank=6 service=ts-food-delivery-service metric=k8s.pod.cpu.usage baseline=0.004681 peak=0.648676 signed_z=999.0 onset_bin=38 onset_rel_s=288.059 persistence_bins=5
values_compact=delta:0.005449,0,-0.001053,-0.000172,0,0.001009,0,0,-0.000993,0.000149,0,0,0.000048,0,0.001329,-0.000942,0,0,-0.000555,0,-0.000017,0,0.00081,-0.000689,0,0.000569,0,-0.00048,0,0.000231,0,0,-0.000416,0,-0.000033,0,0.000404,0,0.322014,0.322014,-0.644184,0,-0.000327,-0.000327,0.000075,0.002201,-0.000699,-0.000698,0,0.000352,0.000004,0.000005,0.000879,0.00088,-0.000424,-0.000423,-0.000761,-0.000761,0,-0.000405,0,0,0.001298,0
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1
[M7] rank=7 service=ts-food-delivery-service metric=k8s.pod.cpu_limit_utilization baseline=0.000936 peak=0.129735 signed_z=999.0 onset_bin=38 onset_rel_s=288.059 persistence_bins=5
values_compact=delta:0.00109,0,-0.000211,-0.000034,0,0.000202,0,0,-0.000199,0.00003,0,0,0.000009,0,0.000266,-0.000188,0,0,-0.000111,0,-0.000004,0,0.000162,-0.000137,0,0.000113,0,-0.000096,0,0.000047,0,0,-0.000084,0,-0.000006,0,0.000081,0,0.064402,0.064403,-0.128837,0,-0.000065,-0.000065,0.000015,0.00044,-0.00014,-0.00014,0,0.000071,0.000001,0.000001,0.000175,0.000176,-0.000084,-0.000085,-0.000152,-0.000152,0,-0.000081,0,0,0.000259,0
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1
[M8] rank=8 service=ts-station-service metric=hubble_http_request_duration_p50_seconds baseline=0.002551 peak=0.375 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.002543,-0.000008,0.00009,-0.000057,0.000068,-0.000136,0,0,0.000278,0.004722,0,0.3675,-0.3725
missing_mask_bits=1011101110111011101110111011101110111111101111111011111110111011
observed_counts_compact=rle:0*1,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*7,1*1,0*7,1*1,0*7,1*1,0*3,1*1,0*2
[M9] rank=9 service=ts-train-service metric=hubble_http_request_duration_p50_seconds baseline=0.002555 peak=10.0 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.002566,-0.000037,0.000052,-0.000081,0.000091,0.00005,-0.000141,0.000032,0.004968,9.9925
missing_mask_bits=1011101110111011101110111011101110111011111111111111111111111111
observed_counts_compact=rle:0*1,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*26
[M10] rank=10 service=ts-train-service metric=hubble_http_request_duration_p99_seconds baseline=0.007849 peak=10.0 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.00805,-0.00235,0.0097,-0.01045,0.003633,0.000479,-0.004112,0.00115,9.8439,0.15
missing_mask_bits=1011101110111011101110111011101110111011111111111111111111111111
observed_counts_compact=rle:0*1,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*26
[M11] rank=11 service=ts-travel-plan-service metric=hubble_http_request_duration_p50_seconds baseline=0.003916 peak=10.0 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.00375,0.000163,-0.000089,0.00004,0.000136,0.000792,-0.001181,-0.00004,9.996429,0,0,0
missing_mask_bits=1011101110111011101110111011101111111011111110111011111110111111
observed_counts_compact=rle:0*1,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*7,1*1,0*7,1*1,0*3,1*1,0*7,1*1,0*6
[M12] rank=12 service=ts-travel-service metric=hubble_http_request_duration_p90_seconds baseline=0.109734 peak=10.0 signed_z=408.068 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.117989,0.002152,-0.020141,0.015833,-0.020409,0.00288,0.061499,-0.089422,-0.000495,9.930114,0,-4.99525,4.99525
missing_mask_bits=0111011101110111011101110111011101110111111111110111011111110111
observed_counts_compact=rle:1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*11,1*1,0*3,1*1,0*7,1*1,0*3

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[222.81727981567383,462.8172798156738]

=== LOG SUMMARY ===
{"entries":[{"error_logs":7737,"error_pct":100.0,"service":"ts-ui-dashboard","total_logs":7737},{"error_logs":342,"error_pct":16.91,"service":"ts-food-service","total_logs":2023},{"error_logs":96,"error_pct":25.0,"service":"ts-notification-service","total_logs":384},{"error_logs":95,"error_pct":25.0,"service":"ts-delivery-service","total_logs":380},{"error_logs":95,"error_pct":4.64,"service":"ts-train-service","total_logs":2046},{"error_logs":92,"error_pct":4.49,"service":"ts-preserve-service","total_logs":2047},{"error_logs":91,"error_pct":1.61,"service":"ts-order-service","total_logs":5665},{"error_logs":11,"error_pct":100.0,"service":"mysql","total_logs":11}],"mode":"errors","omitted_services":24,"service_count":32}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":943710.1,"error_pct":12.08,"p95_during_ms":30005.42552785,"p95_pre_ms":3.1791802999999965,"service":"ts-train-service","spans":9916},{"delta_pct":152455.7,"error_pct":5.02,"p95_during_ms":54851.717669749865,"p95_pre_ms":35.955208,"service":"ts-basic-service","spans":6702},{"delta_pct":15981.4,"error_pct":14.75,"p95_during_ms":60011.692209,"p95_pre_ms":373.1754463999994,"service":"ts-route-plan-service","spans":1668},{"delta_pct":11230.0,"error_pct":14.71,"p95_during_ms":60009.61048685,"p95_pre_ms":529.6522608999998,"service":"ts-travel-plan-service","spans":2187},{"delta_pct":163.8,"error_pct":2.6,"p95_during_ms":223.52072769999634,"p95_pre_ms":84.7412807,"service":"ts-travel-service","spans":8169},{"delta_pct":110.5,"error_pct":2.63,"p95_during_ms":718.3300666499991,"p95_pre_ms":341.26737560000004,"service":"ts-preserve-service","spans":1311},{"delta_pct":101.1,"error_pct":0.0,"p95_during_ms":391.7986182000002,"p95_pre_ms":194.8668118,"service":"ts-ui-dashboard","spans":7737},{"delta_pct":100.1,"error_pct":2.94,"p95_during_ms":393.80692020000015,"p95_pre_ms":196.77570315,"service":"loadgenerator","spans":7737}],"omitted_services":22,"service_count":30}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=35 omitted_edges=13
[{"evidence_source":"trace","onset_rel_s":244.2,"rank":1,"service":"ts-basic-service","severity_z":999.0},{"evidence_source":"trace","onset_rel_s":244.2,"rank":2,"service":"ts-train-service","severity_z":999.0},{"evidence_source":"trace","onset_rel_s":244.2,"rank":3,"service":"ts-travel-plan-service","severity_z":999.0},{"evidence_source":"trace","onset_rel_s":244.2,"rank":4,"service":"ts-travel-service","severity_z":999.0},{"evidence_source":"trace","onset_rel_s":244.2,"rank":5,"service":"ts-route-plan-service","severity_z":875.579},{"evidence_source":"trace","onset_rel_s":244.2,"rank":6,"service":"ts-preserve-service","severity_z":526.614},{"evidence_source":"trace","onset_rel_s":244.2,"rank":7,"service":"loadgenerator","severity_z":414.196},{"evidence_source":"trace","onset_rel_s":244.2,"rank":8,"service":"ts-ui-dashboard","severity_z":414.033},{"evidence_source":"trace","onset_rel_s":264.6,"rank":9,"service":"ts-travel2-service","severity_z":999.0},{"evidence_source":"trace","onset_rel_s":264.6,"rank":10,"service":"ts-seat-service","severity_z":7.061},{"evidence_source":"metric","onset_rel_s":291.6,"rank":11,"service":"ts-food-delivery-service","severity_z":999.0},{"evidence_source":"trace","onset_rel_s":304.2,"rank":12,"service":"ts-station-service","severity_z":938.725},{"evidence_source":"metric","onset_rel_s":394.8,"rank":13,"service":"ts-verification-code-service","severity_z":66.495},{"evidence_source":"metric","onset_rel_s":409.8,"rank":14,"service":"ts-auth-service","severity_z":71.628}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"ts-ui-dashboard","caller":"loadgenerator"},{"callee":"ts-verification-code-service","caller":"ts-auth-service"},{"callee":"ts-station-service","caller":"ts-basic-service"},{"callee":"ts-train-service","caller":"ts-basic-service"},{"callee":"ts-basic-service","caller":"ts-preserve-service"},{"callee":"ts-seat-service","caller":"ts-preserve-service"},{"callee":"ts-travel-service","caller":"ts-preserve-service"},{"callee":"ts-travel-service","caller":"ts-route-plan-service"},{"callee":"ts-travel2-service","caller":"ts-route-plan-service"},{"callee":"ts-route-plan-service","caller":"ts-travel-plan-service"},{"callee":"ts-seat-service","caller":"ts-travel-plan-service"},{"callee":"ts-train-service","caller":"ts-travel-plan-service"},{"callee":"ts-basic-service","caller":"ts-travel-service"},{"callee":"ts-seat-service","caller":"ts-travel-service"},{"callee":"ts-basic-service","caller":"ts-travel2-service"},{"callee":"ts-seat-service","caller":"ts-travel2-service"},{"callee":"ts-auth-service","caller":"ts-ui-dashboard"},{"callee":"ts-preserve-service","caller":"ts-ui-dashboard"},{"callee":"ts-train-service","caller":"ts-ui-dashboard"},{"callee":"ts-travel-plan-service","caller":"ts-ui-dashboard"},{"callee":"ts-travel-service","caller":"ts-ui-dashboard"},{"callee":"ts-travel2-service","caller":"ts-ui-dashboard"},{"callee":"ts-verification-code-service","caller":"ts-ui-dashboard"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

[excluded before optimizer]

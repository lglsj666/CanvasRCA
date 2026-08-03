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
opaque_id: INC-03E6AB7B45D5
observation_window={"duration_rel_s":479.493,"source_metric_rows":1079}
selection_summary={"candidate_count":104,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":1011,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["loadgenerator","loadgenerator-b4559448f-nhzwx","mysql","mysql-0","rabbitmq","rabbitmq-0","ts-admin-basic-info-service","ts-admin-basic-info-service-85cc54c97c-62d58","ts-admin-order-service","ts-admin-order-service-5dc6d7df84-mdgjv","ts-admin-route-service","ts-admin-route-service-67f847dfcc-gcs6d","ts-admin-travel-service","ts-admin-travel-service-8446f69bdd-rt8xm","ts-admin-user-service","ts-admin-user-service-6b4d5494c-pzm86","ts-assurance-service","ts-assurance-service-5775844f55-kv6mf","ts-auth-service","ts-auth-service-6f5b7d4d64-z7z5m","ts-avatar-service","ts-avatar-service-8684d88474-jtzvw","ts-basic-service","ts-basic-service-6d969cd7bd-qc7r4","ts-cancel-service","ts-cancel-service-7566fb95d8-xhfzj","ts-config-service","ts-config-service-78cd5b655b-4mn7n","ts-consign-price-service","ts-consign-price-service-775fc46c9-7jqps","ts-consign-service","ts-consign-service-77655cfd95-nw77m","ts-contacts-service","ts-contacts-service-7c44d4fc9f-25qcq","ts-delivery-service","ts-delivery-service-66b48565c8-jgwkj","ts-execute-service","ts-execute-service-6b8d478797-5lpnq","ts-food-delivery-service","ts-food-delivery-service-df865c857-2xkcv","ts-food-service","ts-food-service-868676c6f4-gx4sk","ts-gateway-service","ts-gateway-service-59bcdc5b64-brs8t","ts-inside-payment-service","ts-inside-payment-service-6d497c8fcc-hfpsj","ts-news-service","ts-news-service-6d6c6d7855-th4vx","ts-notification-service","ts-notification-service-858f6b9957-zd9hg","ts-order-other-service","ts-order-other-service-65f458c7fc-sjcj7","ts-order-service","ts-order-service-687867685d-frtqk","ts-payment-service","ts-payment-service-79b78f9c88-d8d7d","ts-preserve-other-service","ts-preserve-other-service-59ddb7699c-z5sdr","ts-preserve-service","ts-preserve-service-b649b6578-lqff5","ts-price-service","ts-price-service-6b784db86c-7n582","ts-rebook-service","ts-rebook-service-5c7cd6f5cd-8vwbq","ts-route-plan-service","ts-route-plan-service-64f7f6c585-8lql9","ts-route-service","ts-route-service-5cdfd57bd7-dx9dc","ts-seat-service","ts-seat-service-5c44567799-tjtgr","ts-security-service","ts-security-service-74fffc9d56-g4wqz","ts-station-food-service","ts-station-food-service-7f6949d5df-z9587","ts-station-service","ts-station-service-7b75998cfd-wtrp4","ts-ticket-office-service","ts-ticket-office-service-6bf44d54b7-m9ttj","ts-train-food-service","ts-train-food-service-764c49649f-chk4n","ts-train-service","ts-train-service-7fd4bc4b9b-5jqt2","ts-travel-plan-service","ts-travel-plan-service-69865d84f8-s4vjk","ts-travel-service","ts-travel-service-fbbd88b6b-9dx5b","ts-travel2-service","ts-travel2-service-7fd6cf5784-w2jqv","ts-ui-dashboard","ts-ui-dashboard-cdd95b86c-sjlcx","ts-user-service","ts-user-service-5b5b45f5b9-9qttx","ts-verification-code-service","ts-verification-code-service-5cf9cc49d5-p8fc9","ts-voucher-service","ts-voucher-service-cddcc88c5-2xk6x","ts-wait-order-service","ts-wait-order-service-7888ddf9cd-h28hz","worker1","worker2","worker3","worker4","worker5","worker6"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[3.746,11.238,18.73,26.222,33.714,41.206,48.699,56.191,63.683,71.175,78.667,86.159,93.651,101.143,108.635,116.127,123.619,131.111,138.603,146.096,153.588,161.08,168.572,176.064,183.556,191.048,198.54,206.032,213.524,221.016,228.508,236.0,243.493,250.985,258.477,265.969,273.461,280.953,288.445,295.937,303.429,310.921,318.413,325.905,333.398,340.89,348.382,355.874,363.366,370.858,378.35,385.842,393.334,400.826,408.318,415.81,423.302,430.795,438.287,445.779,453.271,460.763,468.255,475.747]
[M1] rank=1 service=ts-ui-dashboard metric=hubble_http_request_duration_p50_seconds baseline=0.015977 peak=7.5 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.013424,0.00567,0.000906,-0.0025,0,-0.004254,0.00012,0.000319,0.005958,-0.002143,-0.003913,7.486413,-7.486658,0.000025,0.000124,-0.005053
missing_mask_bits=0111011101110111011101110111011101110111011101110111011101110111
observed_counts_compact=csv:1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0
[M2] rank=2 service=ts-config-service metric=hubble_http_request_duration_p99_seconds baseline=0.01858 peak=2.11 signed_z=244.398 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.009854,0.013076,-0.00663,0.0033,-0.00435,-0.005845,0.007645,0.0212,2.07175,-2.09055,-0.01445,0.00275,-0.0028,0.003583,-0.003583,0.003617
missing_mask_bits=1101110111011101110111011101110111011101110111011101110111011101
observed_counts_compact=csv:0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0
[M3] rank=3 service=ts-preserve-service metric=k8s.pod.filesystem.usage baseline=999168.0 peak=15560704.0 signed_z=214.795 onset_bin=33 onset_rel_s=250.985 persistence_bins=31
values_compact=delta:892928,6144,6144,8192,4096,2048,6144,14336,6144,10240,6144,4096,4096,2048,10240,4096,8192,2048,2048,10240,6144,10240,14336,12288,4096,14336,6144,16384,4096,8192,8192,4096,57344,227328,161792,356352,204800,346112,415744,448512,616448,448512,382976,501760,583680,567296,550912,421888,393216,540672,524288,458752,491520,591872,473088,407552,542720,458752,405504,526336,559104,526336,542720,489472
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M4] rank=4 service=ts-user-service metric=hubble_http_request_duration_p50_seconds baseline=0.005157 peak=0.375 signed_z=204.614 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.005114,0.001761,0.000511,0.000364,-0.003702,-0.001064,0.000141,0.000846,0.371029,-0.370625,-0.001581,-0.000294,0,0,0
missing_mask_bits=1101110111011101110111011101110111011101110111011111110111011101
observed_counts_compact=rle:0*2,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*7,1*1,0*3,1*1,0*3,1*1,0*1
[M5] rank=5 service=ts-ui-dashboard metric=hubble_http_request_duration_p90_seconds baseline=0.19016 peak=10.0 signed_z=184.646 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.182953,0.084235,-0.035617,0.000855,-0.075888,-0.057316,0.036001,0.080934,9.783843,-9.8375,-0.070167,0.022667,-0.026389,-0.024504,0.027271,0.508622
missing_mask_bits=1110111011101110111011101110111011101110111011101110111011101110
observed_counts_compact=csv:0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1
[M6] rank=6 service=ts-food-delivery-service metric=container.memory.rss baseline=735162455.148936 peak=731373568.0 signed_z=-71.353 onset_bin=50 onset_rel_s=378.35 persistence_bins=14
values_compact=rle:735285248*4,735154176*3,735164416*1,735174656*7,735141888*1,735109120*3,735111168*1,735113216*2,735133696*9,735211520*8,735158272*8,735166464*1,735174656*2,731426816*4,731492352*8,731373568*2
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,2
[M7] rank=7 service=ts-food-delivery-service metric=k8s.pod.memory.rss baseline=735200016.340425 peak=731414528.0 signed_z=-71.297 onset_bin=49 onset_rel_s=370.858 persistence_bins=15
values_compact=delta:735326208,0,0,-65536,-65536,10240,10240,0,0,0,0,0,0,-32768,-32768,0,0,0,0,0,0,4096,0,10240,10240,0,0,0,0,38912,38912,0,0,0,0,0,0,-26624,-26624,0,0,0,0,0,0,0,0,16384,0,-3747840,0,0,0,0,0,32768,32768,0,0,0,0,0,-59392,-59392
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,2
[M8] rank=8 service=ts-price-service metric=container.cpu.usage baseline=0.029517 peak=0.732895 signed_z=68.653 onset_bin=32 onset_rel_s=243.493 persistence_bins=12
values_compact=delta:0.036912,0,-0.004622,0.001109,0.001108,0,-0.012219,0,0.003384,0,-0.00614,0,0,0.004703,0,-0.002184,0,-0.001252,0,0.008473,0.008474,0.021976,0,-0.02044,-0.020271,0,0.014166,0,0,-0.004165,-0.00456,0,0.708443,0,0,-0.701259,0,-0.000361,0.035421,0,-0.02358,0,0,0.020857,-0.006632,0,0.128326,-0.069582,-0.069582,0,0.021881,-0.013816,-0.013816,0.001392,0.001392,0.010028,0,0.148234,0,-0.07336,-0.07336,0,-0.015308,0
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,2
[M9] rank=9 service=ts-price-service metric=hubble_http_request_duration_p99_seconds baseline=0.014277 peak=0.39375 signed_z=64.827 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.00985,0.000088,0,0.011912,-0.011979,0.009579,-0.009933,0.014283,-0.013959,0.012009,-0.0081,0.38,-0.38805,0.00346,-0.001135,0.000608
missing_mask_bits=1101110111011101110111011101110111011101110111011101110111011101
observed_counts_compact=csv:0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0
[M10] rank=10 service=ts-food-delivery-service metric=k8s.pod.memory.node.utilization baseline=0.00553 peak=0.005502 signed_z=-57.007 onset_bin=49 onset_rel_s=370.858 persistence_bins=15
values_compact=rle:0.005531*3,0.00553*11,0.005529*7,0.00553*28,0.005502*6,0.005503*7,0.005502*2
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,2
[M11] rank=11 service=ts-food-delivery-service metric=k8s.pod.memory.available baseline=2474910741.787234 peak=2478706688.0 signed_z=57.007 onset_bin=49 onset_rel_s=370.858 persistence_bins=15
values_compact=delta:2474745856,0,0,90112,90112,-10240,-10240,0,0,0,0,0,0,28672,28672,0,0,0,0,0,0,-4096,0,-6144,-6144,0,0,0,0,-59392,-59392,0,0,0,0,0,0,47104,47104,0,0,0,0,0,0,0,0,-16384,0,3747840,0,0,0,0,0,-53248,-53248,0,0,0,0,0,79872,79872
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,2
[M12] rank=12 service=ts-food-delivery-service metric=k8s.pod.memory.usage baseline=746699754.212766 peak=742903808.0 signed_z=-57.007 onset_bin=49 onset_rel_s=370.858 persistence_bins=15
values_compact=delta:746864640,0,0,-90112,-90112,10240,10240,0,0,0,0,0,0,-28672,-28672,0,0,0,0,0,0,4096,0,6144,6144,0,0,0,0,59392,59392,0,0,0,0,0,0,-47104,-47104,0,0,0,0,0,0,0,0,16384,0,-3747840,0,0,0,0,0,53248,53248,0,0,0,0,0,-79872,-79872
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,2

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[313.00064969062805,478.02516174316406]

=== LOG SUMMARY ===
{"entries":[{"error_logs":5276,"error_pct":100.0,"service":"ts-ui-dashboard","total_logs":5276},{"error_logs":927,"error_pct":10.26,"service":"ts-preserve-service","total_logs":9035},{"error_logs":229,"error_pct":16.05,"service":"ts-food-service","total_logs":1427},{"error_logs":96,"error_pct":25.0,"service":"ts-notification-service","total_logs":384},{"error_logs":96,"error_pct":25.0,"service":"ts-delivery-service","total_logs":384},{"error_logs":69,"error_pct":0.82,"service":"ts-order-service","total_logs":8436}],"mode":"errors","omitted_services":25,"service_count":31}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":1482.5,"error_pct":4.12,"p95_during_ms":5616.7026172499955,"p95_pre_ms":354.92621059999766,"service":"ts-ui-dashboard","spans":5277},{"delta_pct":-82.2,"error_pct":0.0,"p95_during_ms":7.125213899999997,"p95_pre_ms":39.9766955,"service":"ts-consign-service","spans":461},{"delta_pct":-63.8,"error_pct":0.0,"p95_during_ms":451.445885,"p95_pre_ms":1247.1349770999927,"service":"ts-route-plan-service","spans":1238},{"delta_pct":-60.9,"error_pct":0.0,"p95_during_ms":15.9981395,"p95_pre_ms":40.89629969999999,"service":"ts-seat-service","spans":16144},{"delta_pct":-58.8,"error_pct":0.0,"p95_during_ms":689.83868705,"p95_pre_ms":1672.700803400002,"service":"ts-travel-plan-service","spans":1641},{"delta_pct":-48.7,"error_pct":42.88,"p95_during_ms":361.627721,"p95_pre_ms":705.1344572999997,"service":"ts-preserve-service","spans":6854},{"delta_pct":-47.5,"error_pct":0.0,"p95_during_ms":4.32149035,"p95_pre_ms":8.2295645,"service":"ts-assurance-service","spans":504},{"delta_pct":-47.4,"error_pct":0.0,"p95_during_ms":85.37828044999999,"p95_pre_ms":162.4430375,"service":"ts-travel-service","spans":15605}],"omitted_services":22,"service_count":30}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=35 omitted_edges=3
[{"evidence_source":"metric","onset_rel_s":242.4,"rank":1,"service":"ts-travel2-service","severity_z":17.25},{"evidence_source":"metric","onset_rel_s":244.8,"rank":2,"service":"ts-price-service","severity_z":68.653},{"evidence_source":"metric","onset_rel_s":248.4,"rank":3,"service":"ts-train-food-service","severity_z":52.038},{"evidence_source":"metric","onset_rel_s":256.8,"rank":4,"service":"ts-config-service","severity_z":244.398},{"evidence_source":"metric","onset_rel_s":256.8,"rank":5,"service":"ts-security-service","severity_z":51.334},{"evidence_source":"metric","onset_rel_s":257.4,"rank":6,"service":"ts-user-service","severity_z":204.614},{"evidence_source":"metric","onset_rel_s":306.0,"rank":7,"service":"ts-travel-service","severity_z":18.086},{"evidence_source":"metric","onset_rel_s":310.2,"rank":8,"service":"ts-order-service","severity_z":22.897},{"evidence_source":"trace","onset_rel_s":334.8,"rank":9,"service":"ts-ui-dashboard","severity_z":3.946},{"evidence_source":"metric","onset_rel_s":355.2,"rank":10,"service":"ts-station-service","severity_z":14.083},{"evidence_source":"metric","onset_rel_s":373.2,"rank":11,"service":"ts-preserve-service","severity_z":214.795},{"evidence_source":"metric","onset_rel_s":379.2,"rank":12,"service":"ts-food-delivery-service","severity_z":71.353},{"evidence_source":"metric","onset_rel_s":438.6,"rank":13,"service":"ts-route-service","severity_z":34.652},{"evidence_source":"metric","onset_rel_s":466.8,"rank":14,"service":"ts-contacts-service","severity_z":29.171}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"ts-contacts-service","caller":"ts-preserve-service"},{"callee":"ts-order-service","caller":"ts-preserve-service"},{"callee":"ts-security-service","caller":"ts-preserve-service"},{"callee":"ts-travel-service","caller":"ts-preserve-service"},{"callee":"ts-user-service","caller":"ts-preserve-service"},{"callee":"ts-order-service","caller":"ts-security-service"},{"callee":"ts-route-service","caller":"ts-travel-service"},{"callee":"ts-route-service","caller":"ts-travel2-service"},{"callee":"ts-contacts-service","caller":"ts-ui-dashboard"},{"callee":"ts-order-service","caller":"ts-ui-dashboard"},{"callee":"ts-preserve-service","caller":"ts-ui-dashboard"},{"callee":"ts-route-service","caller":"ts-ui-dashboard"},{"callee":"ts-travel-service","caller":"ts-ui-dashboard"},{"callee":"ts-travel2-service","caller":"ts-ui-dashboard"},{"callee":"ts-user-service","caller":"ts-ui-dashboard"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

[excluded before optimizer]

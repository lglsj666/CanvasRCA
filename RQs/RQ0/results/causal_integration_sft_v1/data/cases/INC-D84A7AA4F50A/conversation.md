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
opaque_id: INC-D84A7AA4F50A
observation_window={"duration_rel_s":478.826,"source_metric_rows":1077}
selection_summary={"candidate_count":104,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":1015,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["loadgenerator","loadgenerator-b4559448f-plt6w","mysql","mysql-0","rabbitmq","rabbitmq-0","ts-admin-basic-info-service","ts-admin-basic-info-service-85cc54c97c-b5bb9","ts-admin-order-service","ts-admin-order-service-5dc6d7df84-46qfb","ts-admin-route-service","ts-admin-route-service-67f847dfcc-dptjm","ts-admin-travel-service","ts-admin-travel-service-8446f69bdd-jkc7d","ts-admin-user-service","ts-admin-user-service-6b4d5494c-gmwvg","ts-assurance-service","ts-assurance-service-5775844f55-jbm9r","ts-auth-service","ts-auth-service-6f5b7d4d64-qwhkg","ts-avatar-service","ts-avatar-service-8684d88474-z8g7p","ts-basic-service","ts-basic-service-6d969cd7bd-mv285","ts-cancel-service","ts-cancel-service-7566fb95d8-w9cps","ts-config-service","ts-config-service-78cd5b655b-25ggh","ts-consign-price-service","ts-consign-price-service-775fc46c9-qjqwk","ts-consign-service","ts-consign-service-77655cfd95-6jj5s","ts-contacts-service","ts-contacts-service-7c44d4fc9f-z57qs","ts-delivery-service","ts-delivery-service-66b48565c8-j5d8k","ts-execute-service","ts-execute-service-6b8d478797-tfh2m","ts-food-delivery-service","ts-food-delivery-service-df865c857-rzk8q","ts-food-service","ts-food-service-868676c6f4-rvjpz","ts-gateway-service","ts-gateway-service-59bcdc5b64-xpqxb","ts-inside-payment-service","ts-inside-payment-service-6d497c8fcc-tv947","ts-news-service","ts-news-service-6d6c6d7855-hldjb","ts-notification-service","ts-notification-service-858f6b9957-gclm8","ts-order-other-service","ts-order-other-service-65f458c7fc-s45ld","ts-order-service","ts-order-service-687867685d-7crdd","ts-payment-service","ts-payment-service-79b78f9c88-r5m76","ts-preserve-other-service","ts-preserve-other-service-59ddb7699c-jj22z","ts-preserve-service","ts-preserve-service-b649b6578-nzn9k","ts-price-service","ts-price-service-6b784db86c-ndvbl","ts-rebook-service","ts-rebook-service-5c7cd6f5cd-jflxg","ts-route-plan-service","ts-route-plan-service-64f7f6c585-chbvb","ts-route-service","ts-route-service-5cdfd57bd7-rrrj9","ts-seat-service","ts-seat-service-5c44567799-rnddm","ts-security-service","ts-security-service-74fffc9d56-m7n64","ts-station-food-service","ts-station-food-service-7f6949d5df-zkwdr","ts-station-service","ts-station-service-7b75998cfd-fkk42","ts-ticket-office-service","ts-ticket-office-service-6bf44d54b7-pwhf8","ts-train-food-service","ts-train-food-service-764c49649f-zscfl","ts-train-service","ts-train-service-7fd4bc4b9b-zmh49","ts-travel-plan-service","ts-travel-plan-service-69865d84f8-4kqzn","ts-travel-service","ts-travel-service-fbbd88b6b-56vnh","ts-travel2-service","ts-travel2-service-7fd6cf5784-59gcs","ts-ui-dashboard","ts-ui-dashboard-cdd95b86c-fqph2","ts-user-service","ts-user-service-5b5b45f5b9-b7kb2","ts-verification-code-service","ts-verification-code-service-5cf9cc49d5-pqjtb","ts-voucher-service","ts-voucher-service-cddcc88c5-9s6mm","ts-wait-order-service","ts-wait-order-service-7888ddf9cd-7xm5x","worker1","worker2","worker3","worker4","worker5","worker6"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[3.741,11.222,18.704,26.186,33.667,41.149,48.631,56.112,63.594,71.076,78.557,86.039,93.521,101.002,108.484,115.966,123.447,130.929,138.411,145.892,153.374,160.855,168.337,175.819,183.3,190.782,198.264,205.745,213.227,220.709,228.19,235.672,243.154,250.635,258.117,265.599,273.08,280.562,288.044,295.525,303.007,310.489,317.97,325.452,332.933,340.415,347.897,355.378,362.86,370.342,377.823,385.305,392.787,400.268,407.75,415.232,422.713,430.195,437.677,445.158,452.64,460.122,467.603,475.085]
[M1] rank=1 service=ts-assurance-service-5775844f55-jbm9r metric=k8s.container.ready baseline=1.0 peak=0.0 signed_z=-999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,-1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=1000100010001000100010001000100010001000100010001000100010001000
observed_counts_compact=csv:0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1
[M2] rank=2 service=ts-assurance-service-5775844f55-jbm9r metric=k8s.container.restarts baseline=0.0 peak=1.0 signed_z=999.0 onset_bin=37 onset_rel_s=280.562 persistence_bins=21
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=1000100010001000100010001000100010001000100010001000100010001000
observed_counts_compact=csv:0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1
[M3] rank=3 service=ts-assurance-service metric=hubble_http_request_duration_p90_seconds baseline=0.009234 peak=4.125 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.01175,-0.00475,0.006625,-0.006625,0,0.0055,-0.0055,0.001,4.117,-3.9065,-0.209,0.007,-0.000025,-0.007142,0.000167,0.014
missing_mask_bits=1101110111011101110111011101110111011101110111011101110111011101
observed_counts_compact=csv:0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0
[M4] rank=4 service=ts-assurance-service metric=hubble_http_request_duration_p95_seconds baseline=0.00993 peak=4.5625 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.013375,-0.006125,0.007063,-0.007063,0,0.0065,-0.0065,0.00175,4.5535,-4.32825,-0.2245,0.00725,-0.000012,-0.007321,0.000083,0.0145
missing_mask_bits=1101110111011101110111011110111011101110111011101110111011101110
observed_counts_compact=csv:0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1
[M5] rank=5 service=ts-assurance-service metric=k8s.deployment.available baseline=1.0 peak=0.0 signed_z=-999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,-1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=1000100010001000100010001000100010001000100010001000100010001000
observed_counts_compact=csv:0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1
[M6] rank=6 service=ts-contacts-service metric=hubble_http_request_duration_p90_seconds baseline=0.009409 peak=2.75 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.009481,0.000428,-0.000502,0.000229,-0.000303,-0.000039,-0.000176,-0.000024,0.00085,-0.000944,-0.000083,0.000154,0.000296,0.003633,2.737
missing_mask_bits=1101110111011101110111011101110111011111110111011101110111011101
observed_counts_compact=rle:0*2,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*7,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*1
[M7] rank=7 service=ts-route-service metric=hubble_http_request_duration_p90_seconds baseline=0.014843 peak=1.50875 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.015882,-0.001052,-0.000267,0.000925,-0.000253,-0.00106,-0.000391,0.001007,-0.000309,-0.000276,0.001002,-0.000379,0.000474,1.493447,-1.464375
missing_mask_bits=1101110111011101110111011101110111011111110111011101110111011101
observed_counts_compact=rle:0*2,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*7,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*1
[M8] rank=8 service=ts-route-service metric=hubble_http_request_duration_p95_seconds baseline=0.016309 peak=2.010625 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.017066,-0.000643,-0.000392,0.000502,-0.000165,-0.000176,-0.000512,0.000496,-0.000185,-0.000086,0.001064,-0.000607,0.000086,1.994177,-1.957188
missing_mask_bits=1101110111011101110111011110111011101111111011101110111011101110
observed_counts_compact=rle:0*2,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*4,1*1,0*3,1*1,0*3,1*1,0*7,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1
[M9] rank=9 service=ts-train-food-service metric=hubble_http_request_duration_p99_seconds baseline=0.009794 peak=0.223 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.009875,-0.000004,-0.000013,-0.000083,-0.000058,0.000043,0.000104,-0.000231,0.213367,-0.21805,0.00395,0.00095,0.03865,0.049
missing_mask_bits=1110111011101110111011101110111011111111111011101110111011101110
observed_counts_compact=rle:0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*11,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1
[M10] rank=10 service=ts-ui-dashboard metric=hubble_http_request_duration_p50_seconds baseline=0.00876 peak=6.875 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.008927,-0.00014,-0.000257,0.000106,-0.000043,0.000921,-0.000954,-0.000025,4.991465,1.875,-6.866863,-0.000242,0.000831,-0.000182,0.013269,0.026104
missing_mask_bits=1110111011101110111011101110111011101110111011101110111011101110
observed_counts_compact=csv:0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1
[M11] rank=11 service=ts-assurance-service metric=container.filesystem.usage baseline=466944.0 peak=8376320.0 signed_z=944.254 onset_bin=32 onset_rel_s=243.154 persistence_bins=5
values_compact=rle:466944*32,1773568*1,3080192*1,4188160*1,69632*1,256000*1,442368*2,466944*25
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1
[M12] rank=12 service=ts-verification-code-service metric=hubble_http_request_duration_p95_seconds baseline=0.004797 peak=0.05 signed_z=862.823 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.004863,-0.000113,0,0.000045,0.000048,0.000035,-0.000128,0,0,0,0,0,0.000097,0.007403,0.03775
missing_mask_bits=1101110111011101110111011110111011101111111011101110111011101110
observed_counts_compact=rle:0*2,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*4,1*1,0*3,1*1,0*3,1*1,0*7,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[258.31746792793274,478.32502913475037]

=== LOG SUMMARY ===
{"entries":[{"error_logs":12144,"error_pct":100.0,"service":"ts-ui-dashboard","total_logs":12144},{"error_logs":541,"error_pct":16.82,"service":"ts-food-service","total_logs":3216},{"error_logs":174,"error_pct":5.52,"service":"ts-preserve-service","total_logs":3151},{"error_logs":174,"error_pct":1.84,"service":"ts-order-service","total_logs":9468},{"error_logs":96,"error_pct":25.0,"service":"ts-notification-service","total_logs":384},{"error_logs":96,"error_pct":25.0,"service":"ts-delivery-service","total_logs":384},{"error_logs":10,"error_pct":100.0,"service":"mysql","total_logs":10},{"error_logs":5,"error_pct":0.8,"service":"ts-assurance-service","total_logs":628}],"mode":"errors","omitted_services":24,"service_count":32}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":679.5,"error_pct":0.0,"p95_during_ms":478.6331942,"p95_pre_ms":61.4013878,"service":"ts-cancel-service","spans":36},{"delta_pct":91.7,"error_pct":0.0,"p95_during_ms":16.343701199999995,"p95_pre_ms":8.527606849999998,"service":"ts-assurance-service","spans":1092},{"delta_pct":86.2,"error_pct":0.0,"p95_during_ms":74.69494079999998,"p95_pre_ms":40.1206736,"service":"ts-food-service","spans":3311},{"delta_pct":63.2,"error_pct":0.0,"p95_during_ms":141.58897219999974,"p95_pre_ms":86.767995,"service":"ts-travel-service","spans":13990},{"delta_pct":-49.3,"error_pct":0.0,"p95_during_ms":12.8197371,"p95_pre_ms":25.2927777,"service":"ts-consign-service","spans":1001},{"delta_pct":38.0,"error_pct":0.0,"p95_during_ms":48.778703,"p95_pre_ms":35.3421264,"service":"ts-basic-service","spans":11170},{"delta_pct":29.8,"error_pct":0.0,"p95_during_ms":21.09364904999998,"p95_pre_ms":16.245639399999998,"service":"ts-seat-service","spans":21187},{"delta_pct":26.3,"error_pct":0.0,"p95_during_ms":382.5349849500001,"p95_pre_ms":302.8731355000001,"service":"ts-preserve-service","spans":2041}],"omitted_services":22,"service_count":30}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=35 omitted_edges=4
[{"evidence_source":"trace","onset_rel_s":264.6,"rank":1,"service":"ts-ui-dashboard","severity_z":144.146},{"evidence_source":"trace","onset_rel_s":304.2,"rank":2,"service":"ts-assurance-service","severity_z":261.383},{"evidence_source":"trace","onset_rel_s":304.2,"rank":3,"service":"ts-cancel-service","severity_z":69.363},{"evidence_source":"trace","onset_rel_s":424.2,"rank":4,"service":"ts-route-service","severity_z":18.793},{"evidence_source":"trace","onset_rel_s":424.2,"rank":5,"service":"ts-train-food-service","severity_z":113.277},{"evidence_source":"trace","onset_rel_s":424.2,"rank":6,"service":"ts-seat-service","severity_z":30.403},{"evidence_source":"trace","onset_rel_s":424.2,"rank":7,"service":"ts-travel2-service","severity_z":103.027},{"evidence_source":"trace","onset_rel_s":433.8,"rank":8,"service":"ts-station-service","severity_z":486.018},{"evidence_source":"trace","onset_rel_s":433.8,"rank":9,"service":"ts-basic-service","severity_z":400.095},{"evidence_source":"trace","onset_rel_s":433.8,"rank":10,"service":"loadgenerator","severity_z":52.168},{"evidence_source":"trace","onset_rel_s":433.8,"rank":11,"service":"ts-train-service","severity_z":10.026},{"evidence_source":"trace","onset_rel_s":444.0,"rank":12,"service":"ts-contacts-service","severity_z":24.429},{"evidence_source":"trace","onset_rel_s":444.0,"rank":13,"service":"ts-verification-code-service","severity_z":12.612},{"evidence_source":"metric","onset_rel_s":450.0,"rank":14,"service":"ts-gateway-service","severity_z":119.745}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"ts-ui-dashboard","caller":"loadgenerator"},{"callee":"ts-route-service","caller":"ts-basic-service"},{"callee":"ts-station-service","caller":"ts-basic-service"},{"callee":"ts-train-service","caller":"ts-basic-service"},{"callee":"ts-basic-service","caller":"ts-travel2-service"},{"callee":"ts-route-service","caller":"ts-travel2-service"},{"callee":"ts-seat-service","caller":"ts-travel2-service"},{"callee":"ts-assurance-service","caller":"ts-ui-dashboard"},{"callee":"ts-cancel-service","caller":"ts-ui-dashboard"},{"callee":"ts-contacts-service","caller":"ts-ui-dashboard"},{"callee":"ts-route-service","caller":"ts-ui-dashboard"},{"callee":"ts-train-service","caller":"ts-ui-dashboard"},{"callee":"ts-travel2-service","caller":"ts-ui-dashboard"},{"callee":"ts-verification-code-service","caller":"ts-ui-dashboard"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

{"confidence":"high","reason":"Rank ts-assurance-service first because ts-assurance-service has direct k8s.container.ready evidence (signed-z -999, persistence 0 bins); although ts-ui-dashboard is salient, the caller path ts-ui-dashboard -> ts-assurance-service means a disturbance in the callee can propagate back toward that caller-side symptom.","services":["ts-assurance-service","ts-ui-dashboard"]}

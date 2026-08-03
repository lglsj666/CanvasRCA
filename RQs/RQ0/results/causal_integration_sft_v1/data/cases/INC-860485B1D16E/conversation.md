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
opaque_id: INC-860485B1D16E
observation_window={"duration_rel_s":478.822,"source_metric_rows":1074}
selection_summary={"candidate_count":104,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":997,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["loadgenerator","loadgenerator-b479bdc5c-9n29v","mysql","mysql-0","rabbitmq","rabbitmq-0","ts-admin-basic-info-service","ts-admin-basic-info-service-96954787-qszz6","ts-admin-order-service","ts-admin-order-service-6bcf6ddf78-8dbgc","ts-admin-route-service","ts-admin-route-service-9678dfbb7-9p7h9","ts-admin-travel-service","ts-admin-travel-service-5f7dcc8c78-w788m","ts-admin-user-service","ts-admin-user-service-5b6598696f-2gz4b","ts-assurance-service","ts-assurance-service-5d8974b465-7z2w5","ts-auth-service","ts-auth-service-6d4cb476f4-tbrcm","ts-avatar-service","ts-avatar-service-7d44f9cdb-bcj4s","ts-basic-service","ts-basic-service-67bb4cc894-59njb","ts-cancel-service","ts-cancel-service-c464f54db-42526","ts-config-service","ts-config-service-688bb57f66-rknmw","ts-consign-price-service","ts-consign-price-service-7cd56448d5-v78tf","ts-consign-service","ts-consign-service-858fd6988f-7hbtc","ts-contacts-service","ts-contacts-service-69f8874897-69c2s","ts-delivery-service","ts-delivery-service-8495b4886d-sfnrp","ts-execute-service","ts-execute-service-98d6db6b7-vhjhx","ts-food-delivery-service","ts-food-delivery-service-6965df9cb7-qs6b7","ts-food-service","ts-food-service-5bc8874bdd-r5hhq","ts-gateway-service","ts-gateway-service-7646b44946-rn4k9","ts-inside-payment-service","ts-inside-payment-service-7f65df9f55-lrdth","ts-news-service","ts-news-service-b7d748896-zrdpt","ts-notification-service","ts-notification-service-7f945dc747-c2fnv","ts-order-other-service","ts-order-other-service-bdb88b855-qwzhd","ts-order-service","ts-order-service-6f4cfb5df7-9xq28","ts-payment-service","ts-payment-service-767777d6bb-bwt5t","ts-preserve-other-service","ts-preserve-other-service-6cc7bb5679-b4xhg","ts-preserve-service","ts-preserve-service-c9c68bb7b-vsp6z","ts-price-service","ts-price-service-75f657ff49-9gb4q","ts-rebook-service","ts-rebook-service-58c459f6d-5ppx6","ts-route-plan-service","ts-route-plan-service-6cb49854ff-49w2t","ts-route-service","ts-route-service-5495898fcc-4mxmt","ts-seat-service","ts-seat-service-695f74448f-kwgq5","ts-security-service","ts-security-service-67d6f6c4fd-6fh7j","ts-station-food-service","ts-station-food-service-79b8d75b55-mhhbw","ts-station-service","ts-station-service-5747c84884-2dppl","ts-ticket-office-service","ts-ticket-office-service-f4fcd85cf-cfz7q","ts-train-food-service","ts-train-food-service-cddfc5cd9-jnf4c","ts-train-service","ts-train-service-b7b76f69d-b9ttq","ts-travel-plan-service","ts-travel-plan-service-5c66f9b8dd-2q5mb","ts-travel-service","ts-travel-service-5d8d96b796-t97g7","ts-travel2-service","ts-travel2-service-76d77f447d-bvbvj","ts-ui-dashboard","ts-ui-dashboard-677db5896c-chg78","ts-user-service","ts-user-service-8f5c8f8f5-csw9l","ts-verification-code-service","ts-verification-code-service-7f9b649959-qxjqv","ts-voucher-service","ts-voucher-service-f479849c9-shb2f","ts-wait-order-service","ts-wait-order-service-67c96d8684-pq9sx","worker1","worker2","worker3","worker4","worker5","worker6"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[3.741,11.222,18.704,26.186,33.667,41.149,48.63,56.112,63.594,71.075,78.557,86.038,93.52,101.002,108.483,115.965,123.446,130.928,138.41,145.891,153.373,160.854,168.336,175.818,183.299,190.781,198.262,205.744,213.226,220.707,228.189,235.67,243.152,250.634,258.115,265.597,273.078,280.56,288.042,295.523,303.005,310.486,317.968,325.45,332.931,340.413,347.894,355.376,362.858,370.339,377.821,385.302,392.784,400.266,407.747,415.229,422.71,430.192,437.674,445.155,452.637,460.118,467.6,475.082]
[M1] rank=1 service=ts-basic-service metric=hubble_http_request_duration_p90_seconds baseline=0.009326 peak=0.273167 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.009458,-0.000167,0.000077,-0.000038,-0.00006,0.000024,-0.000198,0.000404,-0.000452,0.117452,-0.007913,0.010163,0.0115,-0.012708,0.134276,0.011349
missing_mask_bits=0111011101110111011101110111011101110111011101110111011101110111
observed_counts_compact=csv:1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0
[M2] rank=2 service=ts-basic-service metric=hubble_http_request_duration_p95_seconds baseline=0.009696 peak=0.51875 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.009785,-0.00014,0.000093,-0.000074,-0.000029,0.000012,-0.000099,0.000358,-0.000221,0.163565,-0.048956,0.067581,0.00575,-0.024167,0.345292,-0.125235
missing_mask_bits=1011101110111011101110111011101110111011101110111011101110111011
observed_counts_compact=csv:0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0
[M3] rank=3 service=ts-verification-code-service metric=hubble_http_request_duration_p95_seconds baseline=0.00475 peak=0.0325 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.00475,0,0,0,0,0,0,0,0,0,0,0,0.02775
missing_mask_bits=1011101110111011101110111011101110111111101110111111101111111011
observed_counts_compact=rle:0*1,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*7,1*1,0*3,1*1,0*7,1*1,0*7,1*1,0*2
[M4] rank=4 service=ts-seat-service metric=hubble_http_request_duration_p99_seconds baseline=0.00985 peak=0.0445 signed_z=822.309 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.009904,-0.000054,0.000038,0.000003,-0.000072,0.000024,-0.000006,-0.00007,0.000126,0.034607
missing_mask_bits=1011101110111011101110111011101110111111111111111111111111111011
observed_counts_compact=rle:0*1,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*27,1*1,0*2
[M5] rank=5 service=loadgenerator metric=hubble_http_request_duration_p90_seconds baseline=0.091258 peak=1.75 signed_z=355.699 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.089615,0.004249,0.004557,-0.012528,0.006799,-0.005692,0.009957,-0.011332,0.010125,1.65425,-1.6725,0.0025
missing_mask_bits=0111011101110111011101110111011101111111111101111111011111110111
observed_counts_compact=rle:1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*11,1*1,0*7,1*1,0*7,1*1,0*3
[M6] rank=6 service=ts-travel2-service metric=hubble_http_request_duration_p50_seconds baseline=0.032688 peak=3.75 signed_z=300.777 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.025,-0.0015,0.014,0.0175,-0.0315,0.0015,-0.003,0.028,-0.02875,3.72875,0,0,-3.7075
missing_mask_bits=1011101110111011101110111101110111011101110111111111110111111101
observed_counts_compact=rle:0*1,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*4,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*11,1*1,0*7,1*1,0*1
[M7] rank=7 service=ts-travel-plan-service metric=hubble_http_request_duration_p90_seconds baseline=0.212188 peak=10.0 signed_z=216.636 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.205,-0.005,0.0625,-0.05,-0.0675,0.0375,0.0075,0.11,-0.041667,9.741667
missing_mask_bits=0111011101110111011101110111011101111111111111111111111111110111
observed_counts_compact=rle:1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*27,1*1,0*3
[M8] rank=8 service=ts-auth-service metric=hubble_http_request_duration_p50_seconds baseline=0.00251 peak=0.0075 signed_z=181.045 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.0025,0,0.000083,-0.000083,0,0,0,0,0,0.0025,-0.00125,0.00375,-0.004821
missing_mask_bits=1011101110111011101110111101110111011111110111111101111111011101
observed_counts_compact=rle:0*1,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*4,1*1,0*3,1*1,0*3,1*1,0*7,1*1,0*7,1*1,0*7,1*1,0*3,1*1,0*1
[M9] rank=9 service=ts-travel2-service metric=hubble_http_request_duration_p90_seconds baseline=0.133932 peak=7.375 signed_z=148.55 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.1525,-0.0575,-0.005,0.1,0.005,-0.126042,0.026042,0.09,7.19,-2.625,0,0,0
missing_mask_bits=1101110111011101110111011101110111111101110111111101111111011101
observed_counts_compact=rle:0*2,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*7,1*1,0*3,1*1,0*7,1*1,0*7,1*1,0*3,1*1,0*1
[M10] rank=10 service=ts-travel2-service metric=hubble_http_request_duration_p95_seconds baseline=0.182044 peak=7.4375 signed_z=109.945 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.20125,-0.10375,0.19,-0.0675,0.0025,-0.119896,0.004896,0.11,7.22,-2.5625,0,0,0
missing_mask_bits=1110111011101110111011101110111011111110111011111110111111101110
observed_counts_compact=rle:0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*7,1*1,0*3,1*1,0*7,1*1,0*7,1*1,0*3,1*1
[M11] rank=11 service=ts-travel-service metric=hubble_http_request_duration_p99_seconds baseline=0.135986 peak=9.85 signed_z=103.775 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.266875,-0.1928,0.056863,-0.056942,0.000165,-0.000069,0.245658,-0.24575,7.4135,-2.5125,0,4.875,-2.3625
missing_mask_bits=1110111011101110111011101110111011101110111111101111111011101111
observed_counts_compact=rle:0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*7,1*1,0*7,1*1,0*3,1*1,0*4
[M12] rank=12 service=ts-station-service metric=hubble_http_request_duration_p99_seconds baseline=0.009582 peak=0.36 signed_z=69.035 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.009821,-0.000183,-0.000488,-0.0012,0.0142,-0.0172,0.0031,-0.0031,0,0.00365,-0.00365,0.00395,0.000562,0.350538,-0.33524
missing_mask_bits=1110111011101110111011101110111011101110111011101110111011101111
observed_counts_compact=rle:0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*4

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[245.68262004852295,455.68262004852295]

=== LOG SUMMARY ===
{"entries":[{"error_logs":3227,"error_pct":100.0,"service":"ts-ui-dashboard","total_logs":3227},{"error_logs":1288,"error_pct":15.02,"service":"ts-basic-service","total_logs":8578},{"error_logs":152,"error_pct":16.07,"service":"ts-food-service","total_logs":946},{"error_logs":96,"error_pct":25.0,"service":"ts-notification-service","total_logs":384},{"error_logs":95,"error_pct":25.0,"service":"ts-delivery-service","total_logs":380},{"error_logs":51,"error_pct":1.29,"service":"ts-travel-service","total_logs":3962},{"error_logs":49,"error_pct":1.79,"service":"ts-order-service","total_logs":2745},{"error_logs":49,"error_pct":4.59,"service":"ts-preserve-service","total_logs":1067}],"mode":"errors","omitted_services":23,"service_count":31}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":14589.0,"error_pct":60.0,"p95_during_ms":60025.86737625,"p95_pre_ms":408.64503899999994,"service":"ts-route-plan-service","spans":748},{"delta_pct":11808.2,"error_pct":60.0,"p95_during_ms":60020.6248053,"p95_pre_ms":504.02761009999995,"service":"ts-travel-plan-service","spans":1037},{"delta_pct":9883.2,"error_pct":0.0,"p95_during_ms":20001.0570035,"p95_pre_ms":200.34804034999976,"service":"ts-ui-dashboard","spans":3227},{"delta_pct":9766.8,"error_pct":7.83,"p95_during_ms":20001.0963491,"p95_pre_ms":202.7113655999993,"service":"loadgenerator","spans":6454},{"delta_pct":4895.9,"error_pct":37.5,"p95_during_ms":4277.11102135,"p95_pre_ms":85.6132635,"service":"ts-travel-service","spans":4414},{"delta_pct":3448.1,"error_pct":37.7,"p95_during_ms":3966.4757175,"p95_pre_ms":111.79015499999996,"service":"ts-travel2-service","spans":2676},{"delta_pct":69.0,"error_pct":0.0,"p95_during_ms":7.042480449999998,"p95_pre_ms":4.167692399999999,"service":"ts-order-service","spans":7383},{"delta_pct":62.9,"error_pct":0.0,"p95_during_ms":9.885840600000003,"p95_pre_ms":6.069383899999997,"service":"ts-route-service","spans":16028}],"omitted_services":22,"service_count":30}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=35 omitted_edges=8
[{"evidence_source":"trace","onset_rel_s":254.4,"rank":1,"service":"ts-travel-service","severity_z":10.41},{"evidence_source":"trace","onset_rel_s":264.6,"rank":2,"service":"loadgenerator","severity_z":371.525},{"evidence_source":"trace","onset_rel_s":264.6,"rank":3,"service":"ts-travel2-service","severity_z":305.418},{"evidence_source":"trace","onset_rel_s":264.6,"rank":4,"service":"ts-ui-dashboard","severity_z":298.203},{"evidence_source":"trace","onset_rel_s":264.6,"rank":5,"service":"ts-train-service","severity_z":19.223},{"evidence_source":"trace","onset_rel_s":394.2,"rank":6,"service":"ts-route-plan-service","severity_z":427.479},{"evidence_source":"trace","onset_rel_s":394.2,"rank":7,"service":"ts-travel-plan-service","severity_z":353.991},{"evidence_source":"trace","onset_rel_s":414.0,"rank":8,"service":"ts-station-service","severity_z":19.482},{"evidence_source":"metric","onset_rel_s":425.4,"rank":9,"service":"ts-basic-service","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":434.4,"rank":10,"service":"ts-auth-service","severity_z":181.045},{"evidence_source":"trace","onset_rel_s":453.6,"rank":11,"service":"ts-verification-code-service","severity_z":86.356},{"evidence_source":"trace","onset_rel_s":453.6,"rank":12,"service":"ts-seat-service","severity_z":10.126},{"evidence_source":"trace","onset_rel_s":453.6,"rank":13,"service":"ts-config-service","severity_z":32.817},{"evidence_source":"metric","onset_rel_s":454.8,"rank":14,"service":"rabbitmq","severity_z":44.194}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"ts-ui-dashboard","caller":"loadgenerator"},{"callee":"ts-verification-code-service","caller":"ts-auth-service"},{"callee":"ts-station-service","caller":"ts-basic-service"},{"callee":"ts-train-service","caller":"ts-basic-service"},{"callee":"ts-travel-service","caller":"ts-route-plan-service"},{"callee":"ts-travel2-service","caller":"ts-route-plan-service"},{"callee":"ts-config-service","caller":"ts-seat-service"},{"callee":"ts-route-plan-service","caller":"ts-travel-plan-service"},{"callee":"ts-seat-service","caller":"ts-travel-plan-service"},{"callee":"ts-train-service","caller":"ts-travel-plan-service"},{"callee":"ts-basic-service","caller":"ts-travel-service"},{"callee":"ts-seat-service","caller":"ts-travel-service"},{"callee":"ts-basic-service","caller":"ts-travel2-service"},{"callee":"ts-seat-service","caller":"ts-travel2-service"},{"callee":"ts-auth-service","caller":"ts-ui-dashboard"},{"callee":"ts-train-service","caller":"ts-ui-dashboard"},{"callee":"ts-travel-plan-service","caller":"ts-ui-dashboard"},{"callee":"ts-travel-service","caller":"ts-ui-dashboard"},{"callee":"ts-travel2-service","caller":"ts-ui-dashboard"},{"callee":"ts-verification-code-service","caller":"ts-ui-dashboard"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

[excluded before optimizer]

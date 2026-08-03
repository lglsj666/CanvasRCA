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
opaque_id: INC-3BAC7B84B9FC
observation_window={"duration_rel_s":479.458,"source_metric_rows":1077}
selection_summary={"candidate_count":104,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":1024,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["loadgenerator","loadgenerator-794b57d884-j7nqw","mysql","mysql-0","rabbitmq","rabbitmq-0","ts-admin-basic-info-service","ts-admin-basic-info-service-8489f5b9dd-k2lwc","ts-admin-order-service","ts-admin-order-service-5b6c548fb5-mklb6","ts-admin-route-service","ts-admin-route-service-6b7fcc6f9b-xb22n","ts-admin-travel-service","ts-admin-travel-service-7d4bb8dcb9-lqbdt","ts-admin-user-service","ts-admin-user-service-5bff4bdf86-c68km","ts-assurance-service","ts-assurance-service-5597965598-wk756","ts-auth-service","ts-auth-service-6d87cc4dc7-5hh8t","ts-avatar-service","ts-avatar-service-7c465d78b5-6jwjj","ts-basic-service","ts-basic-service-6968d4ccd5-bflc7","ts-cancel-service","ts-cancel-service-6cf95f89fc-6j2mh","ts-config-service","ts-config-service-5d4b464d85-4d552","ts-consign-price-service","ts-consign-price-service-7d59bdd47d-c67fs","ts-consign-service","ts-consign-service-848b6d5bcd-hfsqn","ts-contacts-service","ts-contacts-service-55cfbdfdc8-t8rxm","ts-delivery-service","ts-delivery-service-d66597c7f-xlzqc","ts-execute-service","ts-execute-service-6687b7f74d-cqjcx","ts-food-delivery-service","ts-food-delivery-service-bcb844d44-4ks44","ts-food-service","ts-food-service-55f49f6b59-jmjwg","ts-gateway-service","ts-gateway-service-7cc7b478fc-z6rhv","ts-inside-payment-service","ts-inside-payment-service-6d88d7f6b4-bg6wr","ts-news-service","ts-news-service-6d6c6d7855-wkxq5","ts-notification-service","ts-notification-service-596b87f8f6-gf56h","ts-order-other-service","ts-order-other-service-5fc6774cd8-gkztg","ts-order-service","ts-order-service-668587b48c-b6tjs","ts-payment-service","ts-payment-service-7679c6959c-x7h8p","ts-preserve-other-service","ts-preserve-other-service-6bf648d676-qzv9n","ts-preserve-service","ts-preserve-service-5d979f4b55-47x5k","ts-price-service","ts-price-service-55957b666-qnzqx","ts-rebook-service","ts-rebook-service-79d845d787-cv7hb","ts-route-plan-service","ts-route-plan-service-6865bfcc6d-cxc72","ts-route-service","ts-route-service-586ffc746-qstr9","ts-seat-service","ts-seat-service-7b7c5f5d7d-nx4w8","ts-security-service","ts-security-service-5454c847f7-5q28t","ts-station-food-service","ts-station-food-service-cb9656f7b-hmt8v","ts-station-service","ts-station-service-685fd4985f-xtk7d","ts-ticket-office-service","ts-ticket-office-service-9c7b9d55b-wbbzd","ts-train-food-service","ts-train-food-service-bdd545d98-4nck9","ts-train-service","ts-train-service-7b96f444bf-2s9b7","ts-travel-plan-service","ts-travel-plan-service-b49559b55-p2mqn","ts-travel-service","ts-travel-service-56c9999f79-pwr2r","ts-travel2-service","ts-travel2-service-8557fd66df-gh7fm","ts-ui-dashboard","ts-ui-dashboard-68fff76764-8x6fp","ts-user-service","ts-user-service-644dc6f8fb-5hjlj","ts-verification-code-service","ts-verification-code-service-595bc8dd8d-xpjsh","ts-voucher-service","ts-voucher-service-c745bfccb-nzkj6","ts-wait-order-service","ts-wait-order-service-779f77459-hqcxh","worker1","worker2","worker3","worker4","worker5","worker6"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[3.746,11.237,18.729,26.22,33.712,41.203,48.695,56.186,63.678,71.17,78.661,86.153,93.644,101.136,108.627,116.119,123.61,131.102,138.593,146.085,153.576,161.068,168.559,176.051,183.543,191.034,198.526,206.017,213.509,221.0,228.492,235.983,243.475,250.966,258.458,265.949,273.441,280.932,288.424,295.916,303.407,310.899,318.39,325.882,333.373,340.865,348.356,355.848,363.339,370.831,378.322,385.814,393.305,400.797,408.289,415.78,423.272,430.763,438.255,445.746,453.238,460.729,468.221,475.712]
[M1] rank=1 service=ts-basic-service metric=hubble_http_request_duration_p90_seconds baseline=0.006539 peak=0.65225 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.006822,-0.000123,-0.000251,0.000143,0.00003,-0.000454,0.000227,0.00018,-0.000284,-0.000309,0.000002,0.000131,0.000456,0.00716,0.013011,0.625509
missing_mask_bits=0111011101110111011101110111011101110111011101110111011101110111
observed_counts_compact=csv:1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0
[M2] rank=2 service=ts-basic-service metric=hubble_http_request_duration_p95_seconds baseline=0.007057 peak=1.752375 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.007189,-0.00009,-0.000125,0.000299,-0.000212,-0.000228,0.000114,0.000136,-0.000188,-0.000154,0,0.000066,0.000228,0.011729,0.018361,1.71525
missing_mask_bits=1011101110111011101110111011101110111011101110111011101110111011
observed_counts_compact=csv:0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0
[M3] rank=3 service=ts-config-service metric=hubble_http_request_duration_p95_seconds baseline=0.005445 peak=3.0 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.007292,-0.001348,-0.00073,-0.000289,0.000033,0.000459,-0.000539,0.000051,-0.000179,0.00175,-0.00175,2.99525,-2.795
missing_mask_bits=1011101110111011101110111011101110111111101110111111111110111011
observed_counts_compact=rle:0*1,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*7,1*1,0*3,1*1,0*11,1*1,0*3,1*1,0*2
[M4] rank=4 service=ts-price-service metric=hubble_http_request_duration_p90_seconds baseline=0.007849 peak=4.125 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.008636,-0.000565,0.000293,0.000836,-0.00115,-0.00135,0.000467,-0.000567,-0.001993,0.000113,-0.00015,0.000123,0.00195,0.002768,0.032256,4.083333
missing_mask_bits=0111011101110111011101110111011101110111011101110111011101110111
observed_counts_compact=csv:1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0
[M5] rank=5 service=ts-seat-service metric=hubble_http_request_duration_p90_seconds baseline=0.015961 peak=1.991786 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.016102,0.000305,-0.000264,-0.000633,0.000728,-0.000546,0.000042,0.000131,-0.001107,-0.008481,-0.001777,0.0026,-0.0026,0.000265,0.085949,1.901072
missing_mask_bits=0111011101110111011101110111011101110111011101110111011101110111
observed_counts_compact=csv:1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0
[M6] rank=6 service=ts-seat-service metric=hubble_http_request_duration_p95_seconds baseline=0.01676 peak=2.1675 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.016924,-0.000026,-0.00025,0.000283,-0.000218,0.000205,-0.000071,-0.000648,-0.011305,-0.000073,-0.000071,0.018616,-0.010661,0.007545,2.14725,-2.125
missing_mask_bits=1110111011101110111011101110111011101110111011101110111011101110
observed_counts_compact=csv:0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1
[M7] rank=7 service=ts-station-service metric=hubble_http_request_duration_p99_seconds baseline=0.006214 peak=2.29 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.00495,0.004162,-0.001112,-0.00305,0,0,0.0019,-0.0009,-0.001,0.000025,-0.000025,0.00295,0.01635,0.02455,0.0327,2.2085
missing_mask_bits=1110111011101110111011101110111011101110111011101110111011101110
observed_counts_compact=csv:0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1
[M8] rank=8 service=ts-train-service metric=hubble_http_request_duration_p99_seconds baseline=0.006477 peak=2.375 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.008833,0.000548,-0.004431,0.0008,-0.0008,0.0031,-0.0031,0,0.0009,0.17165,-0.172521,0.116021,-0.113075,0.041075,2.326,-2.351436
missing_mask_bits=1110111011101110111011101110111011101110111011101110111011101110
observed_counts_compact=csv:0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1
[M9] rank=9 service=ts-travel-plan-service metric=hubble_http_request_duration_p90_seconds baseline=0.004869 peak=10.0 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.0045,0.00125,-0.001148,-0.000102,0.000113,0.001287,-0.001313,-0.000087,0,0.237625,9.757875
missing_mask_bits=0111011101110111011101110111011101111111111101111111011111111111
observed_counts_compact=rle:1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*11,1*1,0*7,1*1,0*11
[M10] rank=10 service=ts-travel-plan-service metric=hubble_http_request_duration_p95_seconds baseline=0.005764 peak=10.0 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.008125,-0.001333,-0.001943,-0.000099,0.001062,0.000396,-0.001384,-0.000074,0.243875,9.751375
missing_mask_bits=1110111011101110111011101110111011111111111111101111111011111111
observed_counts_compact=rle:0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*15,1*1,0*7,1*1,0*8
[M11] rank=11 service=ts-ui-dashboard metric=hubble_http_request_duration_p90_seconds baseline=0.095774 peak=4.75 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.097264,-0.000864,0.0005,-0.001312,-0.008635,0.014411,-0.005619,0.000235,4.65402,-4.6675,2.9575,-2.805,-0.0525,0.0625
missing_mask_bits=1101110111011101110111011101110111011101110111011101111111011111
observed_counts_compact=rle:0*2,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*7,1*1,0*5
[M12] rank=12 service=ts-verification-code-service metric=hubble_http_request_duration_p95_seconds baseline=0.004757 peak=0.025 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.00475,0,0,0,0,0.000059,-0.000059,0,0,0,0,0.00445,0.000383,0.015417
missing_mask_bits=1011101110111011101110111011101110111111101110111111101110111011
observed_counts_compact=rle:0*1,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*7,1*1,0*3,1*1,0*7,1*1,0*3,1*1,0*3,1*1,0*2

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[337.70609045028687,457.70609045028687]

=== LOG SUMMARY ===
{"entries":[{"error_logs":7654,"error_pct":100.0,"service":"ts-ui-dashboard","total_logs":7654},{"error_logs":1946,"error_pct":17.91,"service":"ts-travel2-service","total_logs":10864},{"error_logs":1944,"error_pct":9.77,"service":"ts-seat-service","total_logs":19904},{"error_logs":351,"error_pct":16.64,"service":"ts-food-service","total_logs":2109},{"error_logs":105,"error_pct":4.86,"service":"ts-preserve-service","total_logs":2161},{"error_logs":105,"error_pct":1.59,"service":"ts-order-service","total_logs":6610},{"error_logs":96,"error_pct":25.0,"service":"ts-delivery-service","total_logs":384},{"error_logs":96,"error_pct":25.0,"service":"ts-notification-service","total_logs":384}],"mode":"errors","omitted_services":23,"service_count":31}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":8976.5,"error_pct":33.33,"p95_during_ms":60016.154058,"p95_pre_ms":661.2282449499997,"service":"ts-travel-plan-service","spans":2550},{"delta_pct":4345.4,"error_pct":0.0,"p95_during_ms":190.17465719999998,"p95_pre_ms":4.277969499999999,"service":"ts-order-other-service","spans":9530},{"delta_pct":2527.6,"error_pct":0.0,"p95_during_ms":1061.3671977999975,"p95_pre_ms":40.3931723,"service":"ts-food-service","spans":2248},{"delta_pct":2313.4,"error_pct":3.37,"p95_during_ms":4984.077236099997,"p95_pre_ms":206.52007969999988,"service":"ts-ui-dashboard","spans":7655},{"delta_pct":2120.3,"error_pct":0.0,"p95_during_ms":120.65521315,"p95_pre_ms":5.4341435,"service":"ts-train-food-service","spans":2470},{"delta_pct":1437.7,"error_pct":3.89,"p95_during_ms":3149.1365809999766,"p95_pre_ms":204.80012359999992,"service":"loadgenerator","spans":7629},{"delta_pct":839.9,"error_pct":0.0,"p95_during_ms":34.668004550000006,"p95_pre_ms":3.6883617999999996,"service":"ts-config-service","spans":17335},{"delta_pct":806.0,"error_pct":0.0,"p95_during_ms":811.6624430999999,"p95_pre_ms":89.58623009999991,"service":"ts-travel-service","spans":10391}],"omitted_services":22,"service_count":30}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=35 omitted_edges=6
[{"evidence_source":"metric","onset_rel_s":260.4,"rank":1,"service":"ts-ui-dashboard","severity_z":999.0},{"evidence_source":"trace","onset_rel_s":344.4,"rank":2,"service":"ts-verification-code-service","severity_z":475.484},{"evidence_source":"trace","onset_rel_s":374.4,"rank":3,"service":"ts-basic-service","severity_z":999.0},{"evidence_source":"trace","onset_rel_s":384.6,"rank":4,"service":"ts-route-service","severity_z":67.61},{"evidence_source":"trace","onset_rel_s":384.6,"rank":5,"service":"ts-route-plan-service","severity_z":12.441},{"evidence_source":"trace","onset_rel_s":394.8,"rank":6,"service":"ts-order-other-service","severity_z":999.0},{"evidence_source":"trace","onset_rel_s":394.8,"rank":7,"service":"ts-order-service","severity_z":999.0},{"evidence_source":"trace","onset_rel_s":394.8,"rank":8,"service":"ts-price-service","severity_z":141.355},{"evidence_source":"trace","onset_rel_s":394.8,"rank":9,"service":"ts-station-service","severity_z":145.695},{"evidence_source":"trace","onset_rel_s":394.8,"rank":10,"service":"ts-train-service","severity_z":65.773},{"evidence_source":"metric","onset_rel_s":395.4,"rank":11,"service":"ts-travel-plan-service","severity_z":999.0},{"evidence_source":"trace","onset_rel_s":414.6,"rank":12,"service":"ts-config-service","severity_z":999.0},{"evidence_source":"trace","onset_rel_s":414.6,"rank":13,"service":"ts-seat-service","severity_z":37.59},{"evidence_source":"trace","onset_rel_s":414.6,"rank":14,"service":"ts-contacts-service","severity_z":67.918}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"ts-price-service","caller":"ts-basic-service"},{"callee":"ts-route-service","caller":"ts-basic-service"},{"callee":"ts-station-service","caller":"ts-basic-service"},{"callee":"ts-train-service","caller":"ts-basic-service"},{"callee":"ts-route-service","caller":"ts-route-plan-service"},{"callee":"ts-config-service","caller":"ts-seat-service"},{"callee":"ts-order-other-service","caller":"ts-seat-service"},{"callee":"ts-order-service","caller":"ts-seat-service"},{"callee":"ts-route-plan-service","caller":"ts-travel-plan-service"},{"callee":"ts-seat-service","caller":"ts-travel-plan-service"},{"callee":"ts-train-service","caller":"ts-travel-plan-service"},{"callee":"ts-contacts-service","caller":"ts-ui-dashboard"},{"callee":"ts-order-other-service","caller":"ts-ui-dashboard"},{"callee":"ts-order-service","caller":"ts-ui-dashboard"},{"callee":"ts-route-service","caller":"ts-ui-dashboard"},{"callee":"ts-train-service","caller":"ts-ui-dashboard"},{"callee":"ts-travel-plan-service","caller":"ts-ui-dashboard"},{"callee":"ts-verification-code-service","caller":"ts-ui-dashboard"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

[excluded before optimizer]

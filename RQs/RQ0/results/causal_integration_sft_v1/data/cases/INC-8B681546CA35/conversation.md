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
opaque_id: INC-8B681546CA35
observation_window={"duration_rel_s":479.744,"source_metric_rows":984}
selection_summary={"candidate_count":103,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":1013,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["loadgenerator","loadgenerator-6cdb67f686-vsc99","mysql","mysql-0","rabbitmq","rabbitmq-0","ts-admin-basic-info-service","ts-admin-basic-info-service-7b9f85b6bb-pk6ml","ts-admin-order-service","ts-admin-order-service-54d769676c-mzz56","ts-admin-route-service","ts-admin-route-service-b4bf97c66-2zhb6","ts-admin-travel-service","ts-admin-travel-service-577df6997f-d4fg8","ts-admin-user-service","ts-admin-user-service-64874ff676-bjspt","ts-assurance-service","ts-assurance-service-f648b466d-l42j4","ts-auth-service","ts-auth-service-5559787bc-jtbb4","ts-avatar-service","ts-avatar-service-5fbddc687f-l8mwz","ts-basic-service","ts-basic-service-56d645df67-68t68","ts-cancel-service","ts-cancel-service-5996849c7f-88qg5","ts-config-service","ts-config-service-7ddf546cff-p6lt9","ts-consign-price-service","ts-consign-price-service-6ff9fc4868-k96kf","ts-consign-service","ts-consign-service-6cfc6565f6-zfkgj","ts-contacts-service","ts-contacts-service-6654bddf5b-ccp8f","ts-delivery-service","ts-delivery-service-684fb959df-549r7","ts-execute-service","ts-execute-service-58686cbccd-fs6d6","ts-food-delivery-service","ts-food-delivery-service-5f698c46db-vr6th","ts-food-service","ts-food-service-5c7888968f-hs5qj","ts-gateway-service","ts-gateway-service-5bdb7dcd99-cfwr5","ts-inside-payment-service","ts-inside-payment-service-79976ffcc4-882l5","ts-news-service","ts-news-service-6d6c6d7855-z9h5v","ts-notification-service","ts-notification-service-5c9f94485d-cwmkz","ts-order-other-service","ts-order-other-service-76658446c4-hncdq","ts-order-service","ts-order-service-7685d896df-jw8pp","ts-payment-service","ts-payment-service-5ff6f7b6ff-bkfrh","ts-preserve-other-service","ts-preserve-other-service-c5c59cfd-d2nsl","ts-preserve-service","ts-preserve-service-657c8cddf7-vxntg","ts-price-service","ts-price-service-6cc5f7ddb8-lmb96","ts-rebook-service","ts-rebook-service-fdff487d9-7w75v","ts-route-plan-service","ts-route-plan-service-64b6ddcbb6-kjwpp","ts-route-service","ts-route-service-664768585b-6dd89","ts-seat-service","ts-seat-service-6c75dd589b-tzlsm","ts-security-service","ts-security-service-765d8f648c-vhzrp","ts-station-food-service","ts-station-food-service-699bcc9cfd-jsk6s","ts-station-service","ts-station-service-7bb69f86cc-kv4mp","ts-ticket-office-service","ts-ticket-office-service-694ff4d646-52p8w","ts-train-food-service","ts-train-food-service-7788f488fb-2mq4q","ts-train-service","ts-train-service-6854555655-nlczf","ts-travel-plan-service","ts-travel-plan-service-646d6b954f-4l6gr","ts-travel-service","ts-travel-service-cbf9bf77c-zfbp4","ts-travel2-service","ts-travel2-service-bc9f9c48c-lblps","ts-ui-dashboard","ts-ui-dashboard-66d999878-8kqzm","ts-user-service","ts-user-service-79d9b5986-s652z","ts-verification-code-service","ts-verification-code-service-7598f57946-s24cj","ts-voucher-service","ts-voucher-service-7d79c7dcbb-lqb48","ts-wait-order-service","ts-wait-order-service-5cc57649b5-cq7rz","worker1","worker2","worker4","worker5","worker6"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[3.748,11.244,18.74,26.236,33.732,41.228,48.724,56.22,63.716,71.212,78.708,86.204,93.7,101.196,108.692,116.188,123.684,131.18,138.676,146.172,153.668,161.164,168.66,176.156,183.652,191.148,198.644,206.14,213.636,221.132,228.628,236.124,243.62,251.116,258.612,266.108,273.604,281.1,288.596,296.092,303.588,311.084,318.58,326.076,333.572,341.068,348.564,356.06,363.556,371.052,378.548,386.044,393.54,401.036,408.532,416.028,423.524,431.02,438.516,446.012,453.508,461.004,468.5,475.996]
[M1] rank=1 service=ts-assurance-service metric=hubble_http_request_duration_p99_seconds baseline=0.017352 peak=0.4225 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.0174,-0.000175,0.000013,0.000147,0.000015,-0.000006,0.000006,-0.000025,0.405125,-0.408625,0.002338,-0.008763,-0.0025,0.190025,-0.185508,0.000108
missing_mask_bits=1101110111011101110111011101110111011101110111011101110111011101
observed_counts_compact=csv:0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0
[M2] rank=2 service=ts-route-plan-service metric=hubble_http_request_duration_p99_seconds baseline=0.014779 peak=0.243725 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.0147,0.000025,-0.000088,0.000113,0.000135,-0.000004,-0.000056,0,-0.000263,0.00015,0.224013,0.005,-0.22905,0.000037,0.000163,0
missing_mask_bits=1101110111011101110111011101110111011101110111011101110111011101
observed_counts_compact=csv:0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0
[M3] rank=3 service=rabbitmq metric=container.memory.available baseline=881525589.333333 peak=878075904.0 signed_z=-718.692 onset_bin=37 onset_rel_s=281.1 persistence_bins=11
values_compact=delta:881537024,0,-8192,0,0,0,-4096,0,2048,2048,0,0,0,0,0,0,0,-2048,-2048,0,0,-2048,-2048,0,0,0,0,0,0,0,0,-4096,4096,0,0,0,0,-14336,-14336,14336,14336,-2048,-2048,0,0,-2048,-2048,4096,0,-262144,0,131072,131072,-3440640,3440640,0,0,0,0,-40960,-40960,0,81920,-34816
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M4] rank=4 service=rabbitmq metric=container.memory.usage baseline=192302250.666667 peak=195751936.0 signed_z=718.692 onset_bin=37 onset_rel_s=281.1 persistence_bins=11
values_compact=delta:192290816,0,8192,0,0,0,4096,0,-2048,-2048,0,0,0,0,0,0,0,2048,2048,0,0,2048,2048,0,0,0,0,0,0,0,0,4096,-4096,0,0,0,0,14336,14336,-14336,-14336,2048,2048,0,0,2048,2048,-4096,0,262144,0,-131072,-131072,3440640,-3440640,0,0,0,0,40960,40960,0,-81920,34816
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M5] rank=5 service=rabbitmq metric=container.memory.working_set baseline=192216234.666667 peak=195665920.0 signed_z=718.692 onset_bin=37 onset_rel_s=281.1 persistence_bins=11
values_compact=delta:192204800,0,8192,0,0,0,4096,0,-2048,-2048,0,0,0,0,0,0,0,2048,2048,0,0,2048,2048,0,0,0,0,0,0,0,0,4096,-4096,0,0,0,0,14336,14336,-14336,-14336,2048,2048,0,0,2048,2048,-4096,0,262144,0,-131072,-131072,3440640,-3440640,0,0,0,0,40960,40960,0,-81920,34816
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M6] rank=6 service=rabbitmq metric=container.memory.rss baseline=152407210.666667 peak=154918912.0 signed_z=672.437 onset_bin=59 onset_rel_s=446.012 persistence_bins=3
values_compact=rle:152403968*17,152406016*1,152408064*3,152410112*1,152412160*21,152414208*1,152416256*9,154918912*1,152416256*5,152455168*1,152494080*2,152416256*1,152418304*1
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M7] rank=7 service=ts-route-plan-service metric=hubble_http_request_duration_p95_seconds baseline=0.013895 peak=0.139875 signed_z=246.148 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.014125,-0.000281,-0.000469,0.000187,0.000688,0.00025,0,-0.0015,0.126875,-0.1265,-0.0015,0.00225,-0.009375,0.00875,0.00025,0.000375
missing_mask_bits=1110111011101110111011101110111011101110111011101110111011101110
observed_counts_compact=csv:0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1
[M8] rank=8 service=ts-user-service metric=hubble_http_request_duration_p99_seconds baseline=0.010636 peak=0.39 signed_z=180.152 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.009937,-0.000187,-0.000108,0.000108,0.000192,0.000003,0.006255,-0.006277,-0.004973,0.004744,-0.000594,-0.001794,-0.002356,0.00165,0.3834,-0.380108
missing_mask_bits=1101110111011101110111011101110111011101110111011101110111011101
observed_counts_compact=csv:0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0
[M9] rank=9 service=ts-config-service metric=hubble_http_request_duration_p99_seconds baseline=0.009108 peak=0.202 signed_z=178.368 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.009671,-0.002971,0.001725,0.0001,0.001392,0.000003,0.000006,-0.000145,-0.004831,0.000047,0.197003,-0.1939,0.001733,-0.000783,0.00071,-0.00031
missing_mask_bits=1101110111011101110111011101110111011101110111011101110111011101
observed_counts_compact=csv:0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0
[M10] rank=10 service=ts-travel-service metric=hubble_http_request_duration_p99_seconds baseline=0.026675 peak=0.475 signed_z=59.418 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.024362,-0.002062,0.0003,0.00105,0.001125,-0.000225,0.02195,-0.021838,-0.014712,0,0,0.01325,-0.00045,0.20175,-0.1998,0.4503
missing_mask_bits=1101110111011101110111011101110111011101110111011101110111011101
observed_counts_compact=csv:0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0
[M11] rank=11 service=ts-assurance-service metric=k8s.pod.filesystem.usage baseline=561066.666667 peak=1204224.0 signed_z=39.333 onset_bin=34 onset_rel_s=258.612 persistence_bins=30
values_compact=delta:528384,0,6144,2048,4096,0,4096,4096,0,4096,2048,2048,2048,2048,4096,0,0,0,0,4096,0,4096,0,0,0,2048,2048,0,4096,0,0,2048,2048,6144,18432,26624,22528,16384,0,16384,12288,20480,28672,12288,16384,40960,24576,18432,18432,28672,20480,18432,18432,20480,32768,26624,18432,6144,14336,24576,20480,10240,26624,24576
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M12] rank=12 service=ts-train-food-service metric=hubble_http_request_duration_p90_seconds baseline=0.009595 peak=0.004821 signed_z=-31.557 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.0095,0.0003,-0.000067,0.000088,-0.000321,0,0,-0.000091,-0.000353,-0.001306,-0.002929,0.003429,-0.00025,0.001,-0.000083,0
missing_mask_bits=1110111011101110111011101110111011101110111011101110111011101110
observed_counts_compact=csv:0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[285.83899974823,375.83899974823]

=== LOG SUMMARY ===
{"entries":[{"error_logs":12496,"error_pct":100.0,"service":"ts-ui-dashboard","total_logs":12496},{"error_logs":491,"error_pct":16.31,"service":"ts-food-service","total_logs":3010},{"error_logs":154,"error_pct":4.73,"service":"ts-preserve-service","total_logs":3253},{"error_logs":154,"error_pct":1.73,"service":"ts-order-service","total_logs":8904},{"error_logs":96,"error_pct":25.0,"service":"ts-notification-service","total_logs":384},{"error_logs":95,"error_pct":25.0,"service":"ts-delivery-service","total_logs":380}],"mode":"errors","omitted_services":25,"service_count":31}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":-44.5,"error_pct":0.0,"p95_during_ms":9.203698,"p95_pre_ms":16.576415,"service":"ts-consign-service","spans":1062},{"delta_pct":-42.4,"error_pct":0.0,"p95_during_ms":3.646311299999996,"p95_pre_ms":6.332323849999999,"service":"ts-assurance-service","spans":4692},{"delta_pct":-38.1,"error_pct":0.0,"p95_during_ms":41.59938759999999,"p95_pre_ms":67.18283879999998,"service":"ts-basic-service","spans":10239},{"delta_pct":-36.4,"error_pct":0.0,"p95_during_ms":97.41894800000001,"p95_pre_ms":153.12222930000024,"service":"ts-travel-service","spans":12952},{"delta_pct":-29.4,"error_pct":0.0,"p95_during_ms":101.76575489999995,"p95_pre_ms":144.073738,"service":"ts-travel2-service","spans":7660},{"delta_pct":-26.6,"error_pct":0.0,"p95_during_ms":45.74977939999999,"p95_pre_ms":62.31574309999997,"service":"ts-food-service","spans":3256},{"delta_pct":-26.3,"error_pct":0.0,"p95_during_ms":4.643123199999995,"p95_pre_ms":6.3006877999999995,"service":"ts-train-food-service","spans":3499},{"delta_pct":-25.7,"error_pct":0.0,"p95_during_ms":661.9987558999999,"p95_pre_ms":890.6226190000002,"service":"ts-travel-plan-service","spans":3336}],"omitted_services":22,"service_count":30}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=35 omitted_edges=3
[{"evidence_source":"trace","onset_rel_s":45.0,"rank":1,"service":"ts-cancel-service","severity_z":57.168},{"evidence_source":"metric","onset_rel_s":255.6,"rank":2,"service":"ts-assurance-service","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":289.2,"rank":3,"service":"ts-travel-plan-service","severity_z":14.255},{"evidence_source":"metric","onset_rel_s":297.6,"rank":4,"service":"ts-admin-order-service","severity_z":17.093},{"evidence_source":"metric","onset_rel_s":315.6,"rank":5,"service":"ts-route-plan-service","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":315.6,"rank":6,"service":"ts-config-service","severity_z":178.368},{"evidence_source":"metric","onset_rel_s":322.8,"rank":7,"service":"ts-train-food-service","severity_z":31.557},{"evidence_source":"metric","onset_rel_s":342.6,"rank":8,"service":"ts-ui-dashboard","severity_z":11.479},{"evidence_source":"metric","onset_rel_s":387.6,"rank":9,"service":"ts-auth-service","severity_z":17.199},{"evidence_source":"metric","onset_rel_s":397.2,"rank":10,"service":"rabbitmq","severity_z":718.692},{"evidence_source":"metric","onset_rel_s":406.8,"rank":11,"service":"ts-inside-payment-service","severity_z":11.446},{"evidence_source":"metric","onset_rel_s":435.6,"rank":12,"service":"ts-user-service","severity_z":180.152},{"evidence_source":"metric","onset_rel_s":465.6,"rank":13,"service":"ts-travel-service","severity_z":59.418},{"evidence_source":"metric","onset_rel_s":474.6,"rank":14,"service":"ts-preserve-service","severity_z":12.256}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"ts-inside-payment-service","caller":"ts-cancel-service"},{"callee":"ts-user-service","caller":"ts-cancel-service"},{"callee":"ts-assurance-service","caller":"ts-preserve-service"},{"callee":"ts-travel-service","caller":"ts-preserve-service"},{"callee":"ts-user-service","caller":"ts-preserve-service"},{"callee":"ts-travel-service","caller":"ts-route-plan-service"},{"callee":"ts-route-plan-service","caller":"ts-travel-plan-service"},{"callee":"ts-assurance-service","caller":"ts-ui-dashboard"},{"callee":"ts-auth-service","caller":"ts-ui-dashboard"},{"callee":"ts-cancel-service","caller":"ts-ui-dashboard"},{"callee":"ts-inside-payment-service","caller":"ts-ui-dashboard"},{"callee":"ts-preserve-service","caller":"ts-ui-dashboard"},{"callee":"ts-travel-plan-service","caller":"ts-ui-dashboard"},{"callee":"ts-travel-service","caller":"ts-ui-dashboard"},{"callee":"ts-user-service","caller":"ts-ui-dashboard"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

[excluded before optimizer]

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
opaque_id: INC-5C40C4B7E169
observation_window={"duration_rel_s":479.846,"source_metric_rows":1064}
selection_summary={"candidate_count":104,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":1000,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["loadgenerator","loadgenerator-6b5db48c4b-rpxlh","mysql","mysql-0","rabbitmq","rabbitmq-0","ts-admin-basic-info-service","ts-admin-basic-info-service-5cc86cdd64-7nd8h","ts-admin-order-service","ts-admin-order-service-74ccdb866f-k6hwk","ts-admin-route-service","ts-admin-route-service-648b6dc6cb-qjpkw","ts-admin-travel-service","ts-admin-travel-service-594d757c69-h6ckr","ts-admin-user-service","ts-admin-user-service-578dd99c6b-9mg64","ts-assurance-service","ts-assurance-service-5f5d76d86-tvsmj","ts-auth-service","ts-auth-service-79597b797c-9cfkk","ts-avatar-service","ts-avatar-service-6cc8c76bb5-vk9nr","ts-basic-service","ts-basic-service-58879bf4df-qqfkk","ts-cancel-service","ts-cancel-service-6c5b744cc-4rdh7","ts-config-service","ts-config-service-59c49c67f7-zsl49","ts-consign-price-service","ts-consign-price-service-6d956db986-8h2np","ts-consign-service","ts-consign-service-cb47df75d-zc2k4","ts-contacts-service","ts-contacts-service-5bd6f6d854-wcx88","ts-delivery-service","ts-delivery-service-655ccb75c5-6sbf9","ts-execute-service","ts-execute-service-568c69c7b8-9c6mt","ts-food-delivery-service","ts-food-delivery-service-bf584dcf6-s9r7k","ts-food-service","ts-food-service-6577cbc5bc-wf2jx","ts-gateway-service","ts-gateway-service-75bf968657-78wwt","ts-inside-payment-service","ts-inside-payment-service-6954f7c664-g9srh","ts-news-service","ts-news-service-7869d45c45-lhqph","ts-notification-service","ts-notification-service-764666799b-sxcpl","ts-order-other-service","ts-order-other-service-cd899d7bd-b8vnj","ts-order-service","ts-order-service-7b574fd599-lxmqv","ts-payment-service","ts-payment-service-5946bfbc65-lzvhf","ts-preserve-other-service","ts-preserve-other-service-7f4d78bb5b-kbsx2","ts-preserve-service","ts-preserve-service-b7646c4c9-f24h6","ts-price-service","ts-price-service-6f5f897546-qrddb","ts-rebook-service","ts-rebook-service-79ff49c795-9j4rw","ts-route-plan-service","ts-route-plan-service-6c7ddb4bc6-bjqwc","ts-route-service","ts-route-service-ccdcbd5c8-5bwmm","ts-seat-service","ts-seat-service-5bd7d4d9c8-9tbbd","ts-security-service","ts-security-service-867fcd9fbf-82j74","ts-station-food-service","ts-station-food-service-5f77969d84-kqqpw","ts-station-service","ts-station-service-84d4687875-zn6wj","ts-ticket-office-service","ts-ticket-office-service-56c759976d-m525b","ts-train-food-service","ts-train-food-service-7bc5dc97bb-gdsfj","ts-train-service","ts-train-service-6ffb8fd6c7-wbdgp","ts-travel-plan-service","ts-travel-plan-service-58ff74775f-gzqzg","ts-travel-service","ts-travel-service-7bf44775ff-bskjx","ts-travel2-service","ts-travel2-service-69454954f-mmtzx","ts-ui-dashboard","ts-ui-dashboard-5b4ff6488d-h7zp8","ts-user-service","ts-user-service-cd75d85d8-rkj25","ts-verification-code-service","ts-verification-code-service-849875c8c6-qrlfp","ts-voucher-service","ts-voucher-service-68944b48-g7qp4","ts-wait-order-service","ts-wait-order-service-865bcf54dc-zmwds","worker1","worker2","worker3","worker4","worker5","worker6"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[3.749,11.246,18.744,26.242,33.739,41.237,48.734,56.232,63.73,71.227,78.725,86.222,93.72,101.218,108.715,116.213,123.71,131.208,138.705,146.203,153.701,161.198,168.696,176.193,183.691,191.189,198.686,206.184,213.681,221.179,228.677,236.174,243.672,251.169,258.667,266.165,273.662,281.16,288.657,296.155,303.653,311.15,318.648,326.145,333.643,341.141,348.638,356.136,363.633,371.131,378.628,386.126,393.624,401.121,408.619,416.116,423.614,431.112,438.609,446.107,453.604,461.102,468.6,476.097]
[M1] rank=1 service=ts-auth-service metric=k8s.pod.filesystem.usage baseline=1148842.666667 peak=22462464.0 signed_z=148.647 onset_bin=32 onset_rel_s=243.672 persistence_bins=32
values_compact=delta:950272,20480,16384,28672,6144,10240,4096,4096,6144,2048,6144,6144,8192,8192,2048,6144,10240,22528,16384,20480,14336,22528,30720,26624,22528,26624,24576,28672,32768,24576,30720,26624,342016,993280,925696,1130496,1083392,1112064,1052672,1097728,921600,921600,968704,1075200,1007616,1081344,1054720,1021952,1021952,1083392,927744,1095680,-4235264,-4251648,956416,1021952,952320,980992,1122304,933888,1200128,1093632,929792,-9306112
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1
[M2] rank=2 service=ts-ui-dashboard metric=hubble_http_request_duration_p90_seconds baseline=0.177168 peak=7.375 signed_z=86.549 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.17517,0.07033,0.071167,-0.075898,-0.050769,-0.102469,0.007469,-0.028295,7.308295,-5.05775,5.05775,-5.089,5.089,-0.05,0.025,-5.03275
missing_mask_bits=1101110111011101110111011101110111011101110111011101110111011101
observed_counts_compact=csv:0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0
[M3] rank=3 service=ts-ui-dashboard metric=hubble_http_request_duration_p95_seconds baseline=0.289558 peak=7.4375 signed_z=44.795 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.230909,0.250341,0.00625,-0.0125,-0.24,-0.138364,0.140864,-0.16483,7.36483,-5.026375,5.026375,-5.042,5.042,-0.025,0.0125,-5.013875
missing_mask_bits=1101110111011101110111011101110111011101110111011101110111011101
observed_counts_compact=csv:0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0
[M4] rank=4 service=ts-avatar-service metric=container.memory.page_faults baseline=48822.06383 peak=49444.0 signed_z=16.03 onset_bin=34 onset_rel_s=258.667 persistence_bins=30
values_compact=rle:48785*2,48787*2,48790*3,48795*6,48797.5*1,48800*7,48871*2,48873.5*1,48876*4,48879*6,48943*2,48946*2,48949*13,49009*2,49010.5*1,49012*1,49444*9
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M5] rank=5 service=ts-avatar-service metric=k8s.pod.memory.page_faults baseline=49514.489362 peak=50134.0 signed_z=16.01 onset_bin=34 onset_rel_s=258.667 persistence_bins=30
values_compact=rle:49475*2,49477*2,49480*2,49485*7,49490*6,49520*1,49550*1,49555.5*1,49561*2,49566*4,49569*6,49633*4,49639*13,49699*2,49702*3,50134*8
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M6] rank=6 service=ts-auth-service metric=k8s.pod.memory.page_faults baseline=173051.208333 peak=184181.0 signed_z=8.283 onset_bin=40 onset_rel_s=303.653 persistence_bins=24
values_compact=delta:170280,815,297,297,0,86,0,0,33,0,48,0,17,0,1989,8,0,0,48,0,360,1,0,39,0,0,36,0,47,0,50,0,23,0,506,117,650.5,650.5,46.5,46.5,787,787,0,19,517.5,517.5,6,6,1051,0,3,0,36,0,1515,0,650.5,650.5,3.5,3.5,5,5,0,1127
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1
[M7] rank=7 service=ts-auth-service metric=container.memory.page_faults baseline=172320.354167 peak=184496.0 signed_z=8.232 onset_bin=41 onset_rel_s=311.15 persistence_bins=23
values_compact=delta:168416,1979,0,663,0,34,0,33,0,48,0,0,17,0,1989,0,18,0,38,359,0,0,35,0,13.5,13.5,15,0,47,0,50,0,23,0,304.5,304.5,662.5,662.5,44.5,44.5,784,784,0,19,510,510,27,0,1051,3,0,0,36,0,1519,0,1296,0,2,12,0,8,0,2121
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1
[M8] rank=8 service=ts-admin-order-service metric=k8s.pod.memory_limit_utilization baseline=0.211468 peak=0.211652 signed_z=7.318 onset_bin=62 onset_rel_s=468.6 persistence_bins=2
values_compact=rle:0.211449*7,0.211488*7,0.21147*1,0.211451*2,0.211452*5,0.211535*2,0.211495*1,0.211455*1,0.211458*1,0.21146*12,0.211474*8,0.211445*9,0.21145*6,0.211652*2
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1
[M9] rank=9 service=ts-admin-order-service metric=k8s.pod.memory.available baseline=2540424448.0 peak=2539831296.0 signed_z=-7.318 onset_bin=62 onset_rel_s=468.6 persistence_bins=2
values_compact=rle:2540486656*7,2540359680*7,2540419072*1,2540478464*2,2540474368*5,2540208128*2,2540337152*1,2540466176*1,2540457984*1,2540449792*12,2540404736*8,2540498944*9,2540482560*6,2539831296*2
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1
[M10] rank=10 service=ts-admin-order-service metric=k8s.pod.memory.usage baseline=681186048.0 peak=681779200.0 signed_z=7.318 onset_bin=62 onset_rel_s=468.6 persistence_bins=2
values_compact=rle:681123840*7,681250816*7,681191424*1,681132032*2,681136128*5,681402368*2,681273344*1,681144320*1,681152512*1,681160704*12,681205760*8,681111552*9,681127936*6,681779200*2
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1
[M11] rank=11 service=ts-admin-order-service metric=k8s.pod.memory.working_set baseline=680801024.0 peak=681394176.0 signed_z=7.318 onset_bin=62 onset_rel_s=468.6 persistence_bins=2
values_compact=rle:680738816*7,680865792*7,680806400*1,680747008*2,680751104*5,681017344*2,680888320*1,680759296*1,680767488*1,680775680*12,680820736*8,680726528*9,680742912*6,681394176*2
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1
[M12] rank=12 service=ts-admin-order-service metric=k8s.pod.memory.node.utilization baseline=0.005045 peak=0.005049 signed_z=7.318 onset_bin=62 onset_rel_s=468.6 persistence_bins=2
values_compact=rle:0.005044*7,0.005045*8,0.005044*7,0.005046*2,0.005045*1,0.005044*2,0.005045*20,0.005044*15,0.005049*2
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[228.90888023376465,468.90888023376465]

=== LOG SUMMARY ===
{"entries":[{"error_logs":4614,"error_pct":100.0,"service":"ts-ui-dashboard","total_logs":4614},{"error_logs":2118,"error_pct":33.49,"service":"ts-auth-service","total_logs":6324},{"error_logs":2118,"error_pct":23.03,"service":"ts-verification-code-service","total_logs":9198},{"error_logs":230,"error_pct":17.32,"service":"ts-food-service","total_logs":1328},{"error_logs":96,"error_pct":25.0,"service":"ts-delivery-service","total_logs":384},{"error_logs":95,"error_pct":25.0,"service":"ts-notification-service","total_logs":380},{"error_logs":51,"error_pct":1.46,"service":"ts-order-service","total_logs":3489},{"error_logs":51,"error_pct":3.99,"service":"ts-preserve-service","total_logs":1279}],"mode":"errors","omitted_services":23,"service_count":31}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":6624.9,"error_pct":5.99,"p95_during_ms":20000.4297715,"p95_pre_ms":297.40975675,"service":"loadgenerator","spans":4493},{"delta_pct":1173.1,"error_pct":23.86,"p95_during_ms":3857.95313675,"p95_pre_ms":303.04796159999944,"service":"ts-ui-dashboard","spans":4615},{"delta_pct":-89.0,"error_pct":70.5,"p95_during_ms":10.349329699999993,"p95_pre_ms":94.3997996,"service":"ts-auth-service","spans":15432},{"delta_pct":-79.6,"error_pct":0.0,"p95_during_ms":7.329640099999999,"p95_pre_ms":35.920540799999976,"service":"ts-consign-service","spans":539},{"delta_pct":-75.6,"error_pct":0.0,"p95_during_ms":16.1715014,"p95_pre_ms":66.40237009999998,"service":"ts-seat-service","spans":7896},{"delta_pct":-74.5,"error_pct":0.0,"p95_during_ms":4.4896422,"p95_pre_ms":17.57315304999989,"service":"ts-price-service","spans":2705},{"delta_pct":-68.1,"error_pct":0.0,"p95_during_ms":3.64494445,"p95_pre_ms":11.415980999999915,"service":"ts-user-service","spans":3685},{"delta_pct":-64.9,"error_pct":0.0,"p95_during_ms":36.284480099999996,"p95_pre_ms":103.481611,"service":"ts-basic-service","spans":4189}],"omitted_services":22,"service_count":30}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=35 omitted_edges=1
[{"evidence_source":"trace","onset_rel_s":244.8,"rank":1,"service":"ts-ui-dashboard","severity_z":3.43},{"evidence_source":"trace","onset_rel_s":244.8,"rank":2,"service":"loadgenerator","severity_z":19.581},{"evidence_source":"metric","onset_rel_s":319.8,"rank":3,"service":"ts-auth-service","severity_z":148.647},{"evidence_source":"metric","onset_rel_s":413.4,"rank":4,"service":"ts-avatar-service","severity_z":16.03},{"evidence_source":"none","onset_rel_s":null,"rank":5,"service":"ts-admin-order-service","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":6,"service":"ts-rebook-service","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":7,"service":"ts-admin-route-service","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":8,"service":"rabbitmq","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":9,"service":"ts-payment-service","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":10,"service":"ts-basic-service","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":11,"service":"ts-route-service","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":12,"service":"ts-admin-basic-info-service","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":13,"service":"ts-gateway-service","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":14,"service":"ts-delivery-service","severity_z":0.0}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"ts-ui-dashboard","caller":"loadgenerator"},{"callee":"ts-route-service","caller":"ts-basic-service"},{"callee":"ts-auth-service","caller":"ts-ui-dashboard"},{"callee":"ts-route-service","caller":"ts-ui-dashboard"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

[excluded before optimizer]

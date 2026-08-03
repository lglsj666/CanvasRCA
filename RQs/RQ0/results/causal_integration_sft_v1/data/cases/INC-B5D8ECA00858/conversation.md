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
opaque_id: INC-B5D8ECA00858
observation_window={"duration_rel_s":479.94,"source_metric_rows":1078}
selection_summary={"candidate_count":104,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":1014,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["loadgenerator","loadgenerator-8465b66847-ns89x","mysql","mysql-0","rabbitmq","rabbitmq-0","ts-admin-basic-info-service","ts-admin-basic-info-service-c7f4d66f9-689s4","ts-admin-order-service","ts-admin-order-service-8578fdc446-hcfbm","ts-admin-route-service","ts-admin-route-service-5d945db787-kdfvr","ts-admin-travel-service","ts-admin-travel-service-96cbcb44b-nptjw","ts-admin-user-service","ts-admin-user-service-5d8d74d79c-ss57d","ts-assurance-service","ts-assurance-service-79876db68f-h9m24","ts-auth-service","ts-auth-service-5dd97d5ccd-cr44x","ts-avatar-service","ts-avatar-service-9b66c896d-9mgs9","ts-basic-service","ts-basic-service-68f7cbd746-fngtv","ts-cancel-service","ts-cancel-service-6cb859955d-jcqj9","ts-config-service","ts-config-service-7c55667486-2w7rj","ts-consign-price-service","ts-consign-price-service-6cffbf7945-v2c8s","ts-consign-service","ts-consign-service-745946dd49-nm7h8","ts-contacts-service","ts-contacts-service-657d4cdfbf-rjk62","ts-delivery-service","ts-delivery-service-6b488868b8-pz4hh","ts-execute-service","ts-execute-service-86d5f5db59-sw96p","ts-food-delivery-service","ts-food-delivery-service-56447bd89f-7nhrc","ts-food-service","ts-food-service-5fd45cf66d-bz8zf","ts-gateway-service","ts-gateway-service-669b9cf6bb-vzqms","ts-inside-payment-service","ts-inside-payment-service-5548965b7f-rx89t","ts-news-service","ts-news-service-6d6c6d7855-rz4h8","ts-notification-service","ts-notification-service-5f7c7d45c9-v9hq2","ts-order-other-service","ts-order-other-service-68fb6fd887-wkjtq","ts-order-service","ts-order-service-56b9db98d8-fhg9l","ts-payment-service","ts-payment-service-7648bd9bcd-d7kfj","ts-preserve-other-service","ts-preserve-other-service-5748c886c9-pm6mr","ts-preserve-service","ts-preserve-service-7684df89bd-c9nf6","ts-price-service","ts-price-service-7494fb49fc-znjxj","ts-rebook-service","ts-rebook-service-546f7bdbbd-bn9s9","ts-route-plan-service","ts-route-plan-service-d9557d6d7-vxj28","ts-route-service","ts-route-service-86dcd6b94f-nl7fb","ts-seat-service","ts-seat-service-75676c6d97-69672","ts-security-service","ts-security-service-7cddbd789d-g2rcn","ts-station-food-service","ts-station-food-service-8c666b479-bggcj","ts-station-service","ts-station-service-7ff47b8db8-qft52","ts-ticket-office-service","ts-ticket-office-service-5c75d795c-vphjv","ts-train-food-service","ts-train-food-service-7b67f6b66f-j8zz7","ts-train-service","ts-train-service-7b65db49f4-m2xnc","ts-travel-plan-service","ts-travel-plan-service-5b7bdc7c56-twlmm","ts-travel-service","ts-travel-service-7f856dcb7b-b7wb2","ts-travel2-service","ts-travel2-service-79fb6f545d-h5lx9","ts-ui-dashboard","ts-ui-dashboard-64f6f55bb5-dm5zr","ts-user-service","ts-user-service-58c56cb98c-tz47b","ts-verification-code-service","ts-verification-code-service-57cddfb855-5c5h6","ts-voucher-service","ts-voucher-service-6b7fbfc649-zfrdw","ts-wait-order-service","ts-wait-order-service-74df69f44-p9m5s","worker1","worker2","worker3","worker4","worker5","worker6"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[3.75,11.249,18.748,26.247,33.746,41.245,48.744,56.243,63.742,71.241,78.74,86.239,93.738,101.237,108.736,116.235,123.734,131.234,138.733,146.232,153.731,161.23,168.729,176.228,183.727,191.226,198.725,206.224,213.723,221.222,228.721,236.22,243.719,251.218,258.717,266.217,273.716,281.215,288.714,296.213,303.712,311.211,318.71,326.209,333.708,341.207,348.706,356.205,363.704,371.203,378.702,386.201,393.701,401.2,408.699,416.198,423.697,431.196,438.695,446.194,453.693,461.192,468.691,476.19]
[M1] rank=1 service=ts-preserve-service metric=k8s.pod.filesystem.usage baseline=1087232.0 peak=22331392.0 signed_z=344.342 onset_bin=32 onset_rel_s=243.719 persistence_bins=32
values_compact=delta:1003520,8192,8192,8192,2048,6144,4096,4096,0,4096,0,2048,2048,4096,4096,0,8192,0,2048,10240,8192,8192,10240,18432,18432,10240,12288,12288,10240,14336,8192,8192,55296,169984,391168,202752,415744,276480,333824,514048,659456,933888,1024000,770048,780288,1132544,1107968,1112064,1112064,923648,872448,1241088,983040,1036288,1030144,1067008,1040384,1261568,-4206592,-4255744,1216512,1032192,872448,1159168
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,1,2,1,2,1,2,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1
[M2] rank=2 service=ts-ui-dashboard metric=hubble_http_request_duration_p50_seconds baseline=0.028994 peak=6.875 signed_z=255.831 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.009859,0.047284,0.024107,-0.035,-0.036841,-0.000266,0.000138,0.000334,0.007885,-0.007578,0.003828,6.73625,-6.741266,0.002203,6.864063,-6.866083
missing_mask_bits=1101110111011101110111011101110111011101110111011101110111011101
observed_counts_compact=csv:0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0
[M3] rank=3 service=ts-train-food-service metric=hubble_http_request_duration_p99_seconds baseline=0.009867 peak=0.0232 signed_z=172.2 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.009864,0.000016,0.00007,0,-0.00003,-0.000203,0.000058,0.000104,0.013321,-0.0133,0,-0.00495,0.0048,0.00005
missing_mask_bits=0111011101110111011101110111011101110111111101110111111101110111
observed_counts_compact=rle:1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*7,1*1,0*3,1*1,0*7,1*1,0*3,1*1,0*3
[M4] rank=4 service=ts-food-service metric=hubble_http_request_duration_p95_seconds baseline=0.011038 peak=0.49875 signed_z=76.725 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.007242,0.006883,0.012625,-0.0195,0.003125,-0.003146,-0.000021,0.000917,0.490625,-0.4915,0.00975,-0.00975,-0.000021
missing_mask_bits=1110111011101110111011101110111011101110111011101111111111101111
observed_counts_compact=rle:0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*11,1*1,0*4
[M5] rank=5 service=ts-security-service metric=k8s.pod.filesystem.usage baseline=669525.333333 peak=1970176.0 signed_z=62.885 onset_bin=34 onset_rel_s=258.717 persistence_bins=30
values_compact=delta:641024,2048,4096,4096,0,0,4096,0,0,0,0,4096,0,0,0,0,4096,0,0,4096,2048,2048,6144,6144,6144,2048,4096,4096,4096,4096,2048,2048,4096,8192,18432,10240,20480,12288,16384,24576,28672,40960,49152,40960,34816,55296,51200,51200,55296,43008,40960,57344,51200,47104,49152,49152,49152,61440,40960,40960,57344,53248,40960,53248
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1
[M6] rank=6 service=ts-preserve-service metric=container.memory.page_faults baseline=143316.083333 peak=178434.0 signed_z=55.609 onset_bin=33 onset_rel_s=251.218 persistence_bins=31
values_compact=delta:142737,117,0,46,0,0,39,0,7,0,25,0,23,0,23,6,0,0,27,19,0,19,0,429,0,452,0,686,0,37,0,98,0,6124,53,53,1463,1463,476.5,476.5,961.5,961.5,5093.5,5093.5,1408.5,1408.5,296,296,51.5,51.5,0,3845,0,0,1034,0,13,0,385,385,2189,0,31,31
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,1,2,1,2,1,2,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1
[M7] rank=7 service=ts-preserve-service metric=k8s.pod.memory.page_faults baseline=144018.583333 peak=179110.0 signed_z=53.479 onset_bin=35 onset_rel_s=266.217 persistence_bins=29
values_compact=delta:143462.5,47.5,27,27,0,55,2,2,0,15.5,15.5,0,23,0,7,0,21.5,21.5,3,3,13.5,13.5,0,440,207,207,346,346,0,69,48,48,63,63,0,6128,0,2914,553.5,553.5,879.5,879.5,5099,5099,1403,1403,311,311,0,83,0,3835,0,0,1034,9,0,0,767,0,2197,0,54,0
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,1,2,1,2,1,2,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1
[M8] rank=8 service=ts-station-service metric=k8s.pod.memory.page_faults baseline=165628.5625 peak=178051.0 signed_z=26.586 onset_bin=39 onset_rel_s=296.213 persistence_bins=25
values_compact=delta:164681,35,0,32,0,44,454,454,31,0,16,8.5,8.5,0,53,0,34,0,12,12,6,6,20,18,0,0,27,34,0,24,5,5,28.5,28.5,13,0,133.5,133.5,0,1512,786,786,27.5,27.5,76,76,10.5,10.5,2110.5,2110.5,0,57,9.5,9.5,10,0,618.5,618.5,728.5,728.5,0,1326,0,55
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,1,2,1,2,1,2,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1
[M9] rank=9 service=ts-station-service metric=container.memory.page_faults baseline=164843.645833 peak=177219.0 signed_z=25.623 onset_bin=39 onset_rel_s=296.213 persistence_bins=25
values_compact=delta:163610.5,283.5,41,0,32,32,907,0,0,38,0,20,0,24,11,0,65,0,12,12,9,9,0,29,0,28,0,36,0,0,30,0,54,0,10.5,10.5,133,133,0,1515,0,1606,0,0,164,0,21,0,2597,0,1639,0,33,33,10.5,10.5,0,1227,727.5,727.5,661,661,16,0
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,1,2,1,2,1,2,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1
[M10] rank=10 service=ts-admin-order-service metric=k8s.pod.memory.available baseline=2548715093.333333 peak=2547871744.0 signed_z=-22.742 onset_bin=44 onset_rel_s=333.708 persistence_bins=3
values_compact=rle:2548711424*5,2548666368*4,2548649984*4,2548699136*1,2548748288*7,2548740096*8,2548738048*1,2548736000*7,2548719616*7,2547871744*3,2548662272*6,2548760576*8,2548736000*3
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M11] rank=11 service=ts-admin-order-service metric=k8s.pod.memory.usage baseline=672895402.666667 peak=673738752.0 signed_z=22.742 onset_bin=44 onset_rel_s=333.708 persistence_bins=3
values_compact=rle:672899072*5,672944128*4,672960512*4,672911360*1,672862208*7,672870400*8,672872448*1,672874496*7,672890880*7,673738752*3,672948224*6,672849920*8,672874496*3
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M12] rank=12 service=ts-admin-order-service metric=k8s.pod.memory.working_set baseline=672510378.666667 peak=673353728.0 signed_z=22.742 onset_bin=44 onset_rel_s=333.708 persistence_bins=3
values_compact=rle:672514048*5,672559104*4,672575488*4,672526336*1,672477184*7,672485376*8,672487424*1,672489472*7,672505856*7,673353728*3,672563200*6,672464896*8,672489472*3
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[317.2670726776123,477.2715504169464]

=== LOG SUMMARY ===
{"entries":[{"error_logs":5638,"error_pct":100.0,"service":"ts-ui-dashboard","total_logs":5638},{"error_logs":1653,"error_pct":11.85,"service":"ts-preserve-service","total_logs":13953},{"error_logs":234,"error_pct":16.36,"service":"ts-food-service","total_logs":1430},{"error_logs":96,"error_pct":25.0,"service":"ts-notification-service","total_logs":384},{"error_logs":96,"error_pct":25.0,"service":"ts-delivery-service","total_logs":384},{"error_logs":68,"error_pct":0.56,"service":"ts-order-service","total_logs":12184}],"mode":"errors","omitted_services":25,"service_count":31}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":968.8,"error_pct":9.79,"p95_during_ms":3173.59435325,"p95_pre_ms":296.9195271999989,"service":"ts-ui-dashboard","spans":5639},{"delta_pct":-76.7,"error_pct":0.0,"p95_during_ms":3.6414912,"p95_pre_ms":15.628937449999984,"service":"ts-assurance-service","spans":476},{"delta_pct":-70.6,"error_pct":0.0,"p95_during_ms":9.219455049999997,"p95_pre_ms":31.368714199999996,"service":"ts-consign-service","spans":453},{"delta_pct":-65.0,"error_pct":0.0,"p95_during_ms":33.1005146,"p95_pre_ms":94.46712204999987,"service":"ts-basic-service","spans":15973},{"delta_pct":-62.8,"error_pct":0.0,"p95_during_ms":14.661142,"p95_pre_ms":39.44828960000001,"service":"ts-seat-service","spans":22010},{"delta_pct":-59.7,"error_pct":49.99,"p95_during_ms":322.4942565,"p95_pre_ms":801.1192561000001,"service":"ts-preserve-service","spans":10334},{"delta_pct":-59.3,"error_pct":0.0,"p95_during_ms":4.1473246,"p95_pre_ms":10.186415749999995,"service":"ts-order-service","spans":39741},{"delta_pct":-57.8,"error_pct":0.0,"p95_during_ms":2.9285854,"p95_pre_ms":6.936722399999988,"service":"ts-train-service","spans":15260}],"omitted_services":22,"service_count":30}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=35 omitted_edges=0
[{"evidence_source":"metric","onset_rel_s":243.6,"rank":1,"service":"ts-train-food-service","severity_z":172.2},{"evidence_source":"metric","onset_rel_s":246.6,"rank":2,"service":"ts-order-service","severity_z":17.811},{"evidence_source":"metric","onset_rel_s":268.2,"rank":3,"service":"ts-food-service","severity_z":76.725},{"evidence_source":"metric","onset_rel_s":310.2,"rank":4,"service":"mysql","severity_z":20.326},{"evidence_source":"metric","onset_rel_s":333.6,"rank":5,"service":"ts-admin-order-service","severity_z":22.742},{"evidence_source":"metric","onset_rel_s":335.4,"rank":6,"service":"ts-preserve-other-service","severity_z":17.449},{"evidence_source":"metric","onset_rel_s":349.8,"rank":7,"service":"ts-travel2-service","severity_z":14.178},{"evidence_source":"metric","onset_rel_s":362.4,"rank":8,"service":"ts-preserve-service","severity_z":344.342},{"evidence_source":"metric","onset_rel_s":367.2,"rank":9,"service":"ts-station-service","severity_z":26.586},{"evidence_source":"metric","onset_rel_s":367.2,"rank":10,"service":"ts-price-service","severity_z":15.474},{"evidence_source":"metric","onset_rel_s":375.0,"rank":11,"service":"ts-contacts-service","severity_z":21.401},{"evidence_source":"metric","onset_rel_s":381.6,"rank":12,"service":"ts-security-service","severity_z":62.885},{"evidence_source":"metric","onset_rel_s":420.0,"rank":13,"service":"ts-config-service","severity_z":22.021},{"evidence_source":"metric","onset_rel_s":439.8,"rank":14,"service":"ts-ui-dashboard","severity_z":255.831}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"ts-train-food-service","caller":"ts-food-service"},{"callee":"ts-contacts-service","caller":"ts-preserve-service"},{"callee":"ts-food-service","caller":"ts-preserve-service"},{"callee":"ts-order-service","caller":"ts-preserve-service"},{"callee":"ts-security-service","caller":"ts-preserve-service"},{"callee":"ts-order-service","caller":"ts-security-service"},{"callee":"ts-contacts-service","caller":"ts-ui-dashboard"},{"callee":"ts-food-service","caller":"ts-ui-dashboard"},{"callee":"ts-order-service","caller":"ts-ui-dashboard"},{"callee":"ts-preserve-service","caller":"ts-ui-dashboard"},{"callee":"ts-travel2-service","caller":"ts-ui-dashboard"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

[excluded before optimizer]

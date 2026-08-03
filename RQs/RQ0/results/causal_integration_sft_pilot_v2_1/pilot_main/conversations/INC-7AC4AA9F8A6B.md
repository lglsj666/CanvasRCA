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
opaque_id: INC-7AC4AA9F8A6B
observation_window={"duration_rel_s":475.964,"source_metric_rows":1074}
selection_summary={"candidate_count":104,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":1017,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["loadgenerator","loadgenerator-b4559448f-qlx8n","mysql","mysql-0","rabbitmq","rabbitmq-0","ts-admin-basic-info-service","ts-admin-basic-info-service-85cc54c97c-2m44f","ts-admin-order-service","ts-admin-order-service-5dc6d7df84-wt2f9","ts-admin-route-service","ts-admin-route-service-67f847dfcc-dgfsg","ts-admin-travel-service","ts-admin-travel-service-8446f69bdd-sxbwn","ts-admin-user-service","ts-admin-user-service-6b4d5494c-dgtkg","ts-assurance-service","ts-assurance-service-5775844f55-9k8rl","ts-auth-service","ts-auth-service-6f5b7d4d64-zdbvd","ts-avatar-service","ts-avatar-service-8684d88474-26jjp","ts-basic-service","ts-basic-service-6d969cd7bd-2hw66","ts-cancel-service","ts-cancel-service-7566fb95d8-8lzt8","ts-config-service","ts-config-service-78cd5b655b-k4vrp","ts-consign-price-service","ts-consign-price-service-775fc46c9-s7sh5","ts-consign-service","ts-consign-service-77655cfd95-8xx7z","ts-contacts-service","ts-contacts-service-7c44d4fc9f-kl2dz","ts-delivery-service","ts-delivery-service-66b48565c8-mb9mn","ts-execute-service","ts-execute-service-6b8d478797-tld8f","ts-food-delivery-service","ts-food-delivery-service-df865c857-xlzdt","ts-food-service","ts-food-service-868676c6f4-7klwl","ts-gateway-service","ts-gateway-service-59bcdc5b64-94wgl","ts-inside-payment-service","ts-inside-payment-service-6d497c8fcc-cq99g","ts-news-service","ts-news-service-6d6c6d7855-vsjms","ts-notification-service","ts-notification-service-858f6b9957-dlp6l","ts-order-other-service","ts-order-other-service-65f458c7fc-fqfnf","ts-order-service","ts-order-service-687867685d-rfmjg","ts-payment-service","ts-payment-service-79b78f9c88-kxh9h","ts-preserve-other-service","ts-preserve-other-service-59ddb7699c-bm4km","ts-preserve-service","ts-preserve-service-b649b6578-4qn9b","ts-price-service","ts-price-service-6b784db86c-qf7sr","ts-rebook-service","ts-rebook-service-5c7cd6f5cd-pngk9","ts-route-plan-service","ts-route-plan-service-64f7f6c585-s9h5z","ts-route-service","ts-route-service-5cdfd57bd7-59s4d","ts-seat-service","ts-seat-service-5c44567799-c6kpn","ts-security-service","ts-security-service-74fffc9d56-khcl9","ts-station-food-service","ts-station-food-service-7f6949d5df-f8484","ts-station-service","ts-station-service-7b75998cfd-4kbsf","ts-ticket-office-service","ts-ticket-office-service-6bf44d54b7-g5nh9","ts-train-food-service","ts-train-food-service-764c49649f-7v55c","ts-train-service","ts-train-service-7fd4bc4b9b-5vqcf","ts-travel-plan-service","ts-travel-plan-service-69865d84f8-gmgrk","ts-travel-service","ts-travel-service-fbbd88b6b-h64vn","ts-travel2-service","ts-travel2-service-7fd6cf5784-pg2gp","ts-ui-dashboard","ts-ui-dashboard-cdd95b86c-xjh5r","ts-user-service","ts-user-service-5b5b45f5b9-rvx6z","ts-verification-code-service","ts-verification-code-service-5cf9cc49d5-28664","ts-voucher-service","ts-voucher-service-cddcc88c5-q7flg","ts-wait-order-service","ts-wait-order-service-7888ddf9cd-szhzq","worker1","worker2","worker3","worker4","worker5","worker6"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[3.718,11.155,18.592,26.029,33.466,40.903,48.34,55.777,63.214,70.651,78.088,85.525,92.962,100.399,107.836,115.272,122.709,130.146,137.583,145.02,152.457,159.894,167.331,174.768,182.205,189.642,197.079,204.516,211.953,219.389,226.826,234.263,241.7,249.137,256.574,264.011,271.448,278.885,286.322,293.759,301.196,308.633,316.07,323.507,330.943,338.38,345.817,353.254,360.691,368.128,375.565,383.002,390.439,397.876,405.313,412.75,420.187,427.624,435.061,442.497,449.934,457.371,464.808,472.245]
[M1] rank=1 service=ts-config-service metric=hubble_http_request_duration_p95_seconds baseline=0.005677 peak=1.75 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.005786,0.00181,-0.000396,-0.002249,-0.000131,-0.00007,0.00075,-0.000683,0.000012,0.004671,-0.004688,0.000142,0.003689,1.741357,-1.728,1.053
missing_mask_bits=1011101110111011101110111011101110111011101110111011101110111011
observed_counts_compact=csv:0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0
[M2] rank=2 service=ts-food-service metric=hubble_http_request_duration_p99_seconds baseline=0.014722 peak=0.462475 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.014825,-0.000075,-0.0003,0.00035,-0.000025,0.000069,0.000037,-0.000431,-0.007,0.455025,-0.44825,0.0003,0.000375,0,0.012325
missing_mask_bits=1101110111011101110111011101110111011111110111011101110111011101
observed_counts_compact=rle:0*2,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*7,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*1
[M3] rank=3 service=ts-route-service metric=hubble_http_request_duration_p90_seconds baseline=0.016109 peak=0.775 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.016469,-0.000073,-0.00037,0.000529,-0.000544,0.000223,-0.000558,-0.00017,0.000327,0.000667,-0.00001,0.000076,-0.000042,0.758476,-0.65875,-0.0605
missing_mask_bits=1011101110111011101110111011101110111011101110111011101110111011
observed_counts_compact=csv:0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0
[M4] rank=4 service=ts-route-service metric=hubble_http_request_duration_p95_seconds baseline=0.016852 peak=1.8625 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.017032,-0.000067,-0.000176,0.000447,-0.000461,0.000156,-0.000343,-0.000085,0.000191,0.000306,-0.000005,0.041633,-0.041531,1.845403,-1.716875,-0.0865
missing_mask_bits=1011101110111011101110111011101110111011101110111011101110111011
observed_counts_compact=csv:0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0
[M5] rank=5 service=ts-seat-service metric=hubble_http_request_duration_p90_seconds baseline=0.023735 peak=2.05 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.023962,-0.000255,0.000211,-0.000294,0.000105,0.000021,-0.000412,0.000512,-0.0001,-0.0075,0.007191,0.000223,0.020086,0.05625,1.95
missing_mask_bits=1011101110111011101110111011101110111011111110111011101110111011
observed_counts_compact=rle:0*1,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*7,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*2
[M6] rank=6 service=ts-seat-service metric=hubble_http_request_duration_p95_seconds baseline=0.024445 peak=0.21625 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.02425,0,0.000207,0.000034,-0.00026,0.000214,0.000237,0.000071,-0.007878,0.007535,-0.000177,0.018017,0.174,-0.120694,-0.018056
missing_mask_bits=1110111011101110111011101110111011111110111011101110111011101110
observed_counts_compact=rle:0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*7,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1
[M7] rank=7 service=ts-station-service metric=hubble_http_request_duration_p95_seconds baseline=0.005317 peak=1.75 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.007417,-0.001717,-0.000743,0.000035,-0.000102,0,0.00005,-0.00019,0,0,0,0,0.0018,1.74345,-1.72,-0.0125
missing_mask_bits=1011101110111011101110111011101110111011101110111011101110111011
observed_counts_compact=csv:0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0
[M8] rank=8 service=ts-travel-plan-service metric=hubble_http_request_duration_p90_seconds baseline=0.014207 peak=1.10225 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.014218,-0.000074,0.000149,0.000178,-0.000201,-0.000143,-0.000127,0.000135,0.000064,-0.000199,0.000101,0.028149,0.085,0.975
missing_mask_bits=1011101110111011101110111011101110111111111110111011101110111011
observed_counts_compact=rle:0*1,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*11,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*2
[M9] rank=9 service=ts-travel-service-fbbd88b6b-h64vn metric=k8s.container.restarts baseline=0.0 peak=1.0 signed_z=999.0 onset_bin=35 onset_rel_s=264.011 persistence_bins=22
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0001000100100010001000100010001000100010001000100100010001000100
observed_counts_compact=csv:1,1,1,0,1,1,1,0,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1
[M10] rank=10 service=ts-travel-service metric=hubble_http_request_duration_p90_seconds baseline=0.035166 peak=1.75 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.035283,-0.000343,-0.000035,0.000178,0.00022,0.000418,-0.000523,-0.0003,-0.000509,0.189361,-0.01875,-0.170068,-0.000027,1.715095,-1.5525,-0.06875
missing_mask_bits=1011101110111011101110111011101110111011101110111011101110111011
observed_counts_compact=csv:0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0
[M11] rank=11 service=ts-travel2-service metric=hubble_http_request_duration_p90_seconds baseline=0.047797 peak=1.6 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.0465,0.001,0.001618,-0.000837,-0.00125,0.001441,0.000392,-0.002257,0.00131,0.427083,-0.427187,0,1.552187,-1.37625,-0.00375
missing_mask_bits=1011101110111011101110111011101110111011111110111011101110111011
observed_counts_compact=rle:0*1,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*7,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*2
[M12] rank=12 service=ts-ui-dashboard metric=hubble_http_request_duration_p50_seconds baseline=0.009237 peak=4.375 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.009261,-0.000021,-0.00017,0.000074,0.000299,-0.000092,-0.000472,0.000629,-0.000332,4.365824,-4.363125,-0.002931,0.00017,0.007275,0.024682,0.00754
missing_mask_bits=0111011101110111011101110111011101110111011101110111011101110111
observed_counts_compact=csv:1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[256.3468849658966,346.3468849658966]

=== LOG SUMMARY ===
{"entries":[{"error_logs":10358,"error_pct":100.0,"service":"ts-ui-dashboard","total_logs":10358},{"error_logs":480,"error_pct":16.74,"service":"ts-food-service","total_logs":2868},{"error_logs":164,"error_pct":5.65,"service":"ts-preserve-service","total_logs":2905},{"error_logs":164,"error_pct":1.92,"service":"ts-order-service","total_logs":8548},{"error_logs":95,"error_pct":25.0,"service":"ts-notification-service","total_logs":380},{"error_logs":95,"error_pct":25.0,"service":"ts-delivery-service","total_logs":380},{"error_logs":17,"error_pct":1.01,"service":"ts-route-plan-service","total_logs":1677},{"error_logs":10,"error_pct":0.09,"service":"ts-travel-service","total_logs":11337}],"mode":"errors","omitted_services":24,"service_count":32}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":489.2,"error_pct":15.14,"p95_during_ms":3572.0861682,"p95_pre_ms":606.2900237999999,"service":"ts-route-plan-service","spans":2440},{"delta_pct":-50.9,"error_pct":0.0,"p95_during_ms":15.781601,"p95_pre_ms":32.15250344999995,"service":"ts-seat-service","spans":18949},{"delta_pct":-34.7,"error_pct":0.0,"p95_during_ms":35.427471499999996,"p95_pre_ms":54.23634989999987,"service":"ts-basic-service","spans":9886},{"delta_pct":-32.5,"error_pct":0.0,"p95_during_ms":288.317265,"p95_pre_ms":427.2696172999995,"service":"ts-preserve-service","spans":1884},{"delta_pct":-30.3,"error_pct":0.0,"p95_during_ms":10.084652049999999,"p95_pre_ms":14.471293299999996,"service":"ts-consign-service","spans":974},{"delta_pct":-22.5,"error_pct":0.0,"p95_during_ms":6.020294599999997,"p95_pre_ms":7.763768199999996,"service":"ts-route-service","spans":49480},{"delta_pct":-22.4,"error_pct":0.0,"p95_during_ms":7.306544099999996,"p95_pre_ms":9.411009649999988,"service":"ts-assurance-service","spans":952},{"delta_pct":-22.1,"error_pct":0.0,"p95_during_ms":4.498058599999999,"p95_pre_ms":5.775979499999999,"service":"ts-train-food-service","spans":3468}],"omitted_services":22,"service_count":30}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=35 omitted_edges=10
[{"evidence_source":"trace","onset_rel_s":262.8,"rank":1,"service":"ts-ui-dashboard","severity_z":294.537},{"evidence_source":"trace","onset_rel_s":272.4,"rank":2,"service":"ts-travel2-service","severity_z":141.646},{"evidence_source":"trace","onset_rel_s":272.4,"rank":3,"service":"loadgenerator","severity_z":301.203},{"evidence_source":"trace","onset_rel_s":272.4,"rank":4,"service":"ts-basic-service","severity_z":74.829},{"evidence_source":"trace","onset_rel_s":302.4,"rank":5,"service":"ts-food-service","severity_z":12.703},{"evidence_source":"trace","onset_rel_s":302.4,"rank":6,"service":"ts-travel-service","severity_z":53.407},{"evidence_source":"trace","onset_rel_s":381.6,"rank":7,"service":"ts-config-service","severity_z":106.384},{"evidence_source":"trace","onset_rel_s":381.6,"rank":8,"service":"ts-route-service","severity_z":68.251},{"evidence_source":"trace","onset_rel_s":381.6,"rank":9,"service":"ts-seat-service","severity_z":999.0},{"evidence_source":"trace","onset_rel_s":391.8,"rank":10,"service":"ts-station-service","severity_z":999.0},{"evidence_source":"trace","onset_rel_s":391.8,"rank":11,"service":"ts-order-service","severity_z":337.159},{"evidence_source":"trace","onset_rel_s":411.6,"rank":12,"service":"ts-verification-code-service","severity_z":4.999},{"evidence_source":"metric","onset_rel_s":415.8,"rank":13,"service":"ts-inside-payment-service","severity_z":226.46},{"evidence_source":"metric","onset_rel_s":458.4,"rank":14,"service":"ts-travel-plan-service","severity_z":999.0}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"ts-ui-dashboard","caller":"loadgenerator"},{"callee":"ts-route-service","caller":"ts-basic-service"},{"callee":"ts-station-service","caller":"ts-basic-service"},{"callee":"ts-travel-service","caller":"ts-food-service"},{"callee":"ts-order-service","caller":"ts-inside-payment-service"},{"callee":"ts-config-service","caller":"ts-seat-service"},{"callee":"ts-order-service","caller":"ts-seat-service"},{"callee":"ts-seat-service","caller":"ts-travel-plan-service"},{"callee":"ts-basic-service","caller":"ts-travel-service"},{"callee":"ts-route-service","caller":"ts-travel-service"},{"callee":"ts-seat-service","caller":"ts-travel-service"},{"callee":"ts-basic-service","caller":"ts-travel2-service"},{"callee":"ts-route-service","caller":"ts-travel2-service"},{"callee":"ts-seat-service","caller":"ts-travel2-service"},{"callee":"ts-food-service","caller":"ts-ui-dashboard"},{"callee":"ts-inside-payment-service","caller":"ts-ui-dashboard"},{"callee":"ts-order-service","caller":"ts-ui-dashboard"},{"callee":"ts-route-service","caller":"ts-ui-dashboard"},{"callee":"ts-travel-plan-service","caller":"ts-ui-dashboard"},{"callee":"ts-travel-service","caller":"ts-ui-dashboard"},{"callee":"ts-travel2-service","caller":"ts-ui-dashboard"},{"callee":"ts-verification-code-service","caller":"ts-ui-dashboard"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

{"confidence":"high","reason":"Rank ts-travel-service first because ts-travel-service has direct hubble_http_request_duration_p90_seconds evidence (signed-z 999, persistence 0 bins); although ts-ui-dashboard is salient, the caller path ts-ui-dashboard -> ts-travel-service means a disturbance in the callee can propagate back toward that caller-side symptom. The remaining entries preserve evidence-supported alternatives so the ranking retains calibrated uncertainty instead of collapsing to one answer.","services":["ts-travel-service","ts-travel-service-fbbd88b6b-h64vn","ts-travel2-service","ts-ui-dashboard","ts-basic-service"]}

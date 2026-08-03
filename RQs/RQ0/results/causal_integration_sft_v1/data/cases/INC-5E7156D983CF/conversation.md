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
opaque_id: INC-5E7156D983CF
observation_window={"duration_rel_s":477.331,"source_metric_rows":1064}
selection_summary={"candidate_count":104,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":1004,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["loadgenerator","loadgenerator-785d5fb59-fmpv4","mysql","mysql-0","rabbitmq","rabbitmq-0","ts-admin-basic-info-service","ts-admin-basic-info-service-b895cdd69-287g9","ts-admin-order-service","ts-admin-order-service-7875cc9676-9wwmg","ts-admin-route-service","ts-admin-route-service-65cc8cd669-6rl85","ts-admin-travel-service","ts-admin-travel-service-79487c5956-z5kfl","ts-admin-user-service","ts-admin-user-service-58ffc9f45f-t67md","ts-assurance-service","ts-assurance-service-94c7df99f-psx5p","ts-auth-service","ts-auth-service-77d85c69dd-m5wwc","ts-avatar-service","ts-avatar-service-7c7c4d64b6-gvkqh","ts-basic-service","ts-basic-service-5bdf7474bd-xgh27","ts-cancel-service","ts-cancel-service-66bcbdcdb8-hwjg2","ts-config-service","ts-config-service-7686c57bbd-xmt4c","ts-consign-price-service","ts-consign-price-service-585746d54c-gb586","ts-consign-service","ts-consign-service-5b4fc59b95-l9zh5","ts-contacts-service","ts-contacts-service-5f977d6595-ddwk6","ts-delivery-service","ts-delivery-service-574b957b7d-k54wc","ts-execute-service","ts-execute-service-55c8b8c85c-bjq2v","ts-food-delivery-service","ts-food-delivery-service-6fdbfd8b5-j6knz","ts-food-service","ts-food-service-5c89cbd9b6-ndgfr","ts-gateway-service","ts-gateway-service-6b447657b4-k2fk4","ts-inside-payment-service","ts-inside-payment-service-865c45d45-jn72l","ts-news-service","ts-news-service-7869d45c45-dszwj","ts-notification-service","ts-notification-service-59744d66d5-rpjj9","ts-order-other-service","ts-order-other-service-54467c8fd5-9xxf2","ts-order-service","ts-order-service-66c6db4f9d-xgg4h","ts-payment-service","ts-payment-service-76f8cc59b8-2n5mw","ts-preserve-other-service","ts-preserve-other-service-7c564bfbf7-9tdjf","ts-preserve-service","ts-preserve-service-84ccbbd47d-9spqh","ts-price-service","ts-price-service-74c479b7f9-k5qrc","ts-rebook-service","ts-rebook-service-58c78d4854-pqbzb","ts-route-plan-service","ts-route-plan-service-67d8f8fbbf-mc8vr","ts-route-service","ts-route-service-f6fbc58bc-54x8k","ts-seat-service","ts-seat-service-5d77c89dc-btxkd","ts-security-service","ts-security-service-6ccc7f574d-xbpwf","ts-station-food-service","ts-station-food-service-6946c6dbf7-62gth","ts-station-service","ts-station-service-6d7c454d54-k77ts","ts-ticket-office-service","ts-ticket-office-service-58645d4ff-s9pjr","ts-train-food-service","ts-train-food-service-5d47bdcd87-b5z8q","ts-train-service","ts-train-service-7c76856-ls7wp","ts-travel-plan-service","ts-travel-plan-service-6f7bb6dccd-8gsfq","ts-travel-service","ts-travel-service-669d7cb98b-vgplm","ts-travel2-service","ts-travel2-service-8597bd544d-fcc8l","ts-ui-dashboard","ts-ui-dashboard-7b6fff4695-x88xj","ts-user-service","ts-user-service-74d64f7bf7-gx58w","ts-verification-code-service","ts-verification-code-service-86c65784d9-njbxq","ts-voucher-service","ts-voucher-service-58698784bc-vh5rn","ts-wait-order-service","ts-wait-order-service-6cd9578878-ctwxn","worker1","worker2","worker3","worker4","worker5","worker6"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[3.729,11.187,18.646,26.104,33.562,41.021,48.479,55.937,63.396,70.854,78.312,85.77,93.229,100.687,108.145,115.604,123.062,130.52,137.979,145.437,152.895,160.353,167.812,175.27,182.728,190.187,197.645,205.103,212.561,220.02,227.478,234.936,242.395,249.853,257.311,264.77,272.228,279.686,287.144,294.603,302.061,309.519,316.978,324.436,331.894,339.353,346.811,354.269,361.727,369.186,376.644,384.102,391.561,399.019,406.477,413.936,421.394,428.852,436.31,443.769,451.227,458.685,466.144,473.602]
[M1] rank=1 service=ts-seat-service metric=hubble_http_request_duration_p50_seconds baseline=0.025914 peak=10.0 signed_z=754.264 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.014764,-0.002311,0.000049,0.000362,0.023403,0.007938,-0.00208,-0.009993,-0.016382,9.98425,0,-9.97
missing_mask_bits=1011101110111011101110111011101110111111111111111011101111111011
observed_counts_compact=rle:0*1,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*15,1*1,0*3,1*1,0*7,1*1,0*2
[M2] rank=2 service=ts-order-other-service metric=hubble_http_request_duration_p95_seconds baseline=0.019719 peak=10.0 signed_z=746.089 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.016,-0.006321,-0.000299,-0.000551,0.000997,0.038924,-0.017563,-0.007087,-0.014506,9.990406
missing_mask_bits=0111011101110111011101110111011101111111111111111111011111111111
observed_counts_compact=rle:1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*19,1*1,0*11
[M3] rank=3 service=ts-order-other-service metric=hubble_http_request_duration_p99_seconds baseline=0.023268 peak=10.0 signed_z=666.414 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.007451,0.002449,-0.000122,0.013235,0.006212,0.016275,0.001625,-0.032975,9.98585
missing_mask_bits=1110111011101110111011101110111011111111111111111111111011111111
observed_counts_compact=rle:0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*23,1*1,0*8
[M4] rank=4 service=ts-travel-plan-service metric=hubble_http_request_duration_p50_seconds baseline=0.039515 peak=10.0 signed_z=390.191 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.025,-0.01117,0,0.000483,0.03796,0.010227,0.025,-0.040625,-0.029375,9.9825
missing_mask_bits=1011101110111011101110111011101110111111111111111011111111111111
observed_counts_compact=rle:0*1,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*15,1*1,0*14
[M5] rank=5 service=ts-seat-service metric=hubble_http_request_duration_p90_seconds baseline=0.06135 peak=10.0 signed_z=211.712 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.062016,-0.045228,-0.00022,0.000011,0.014773,0.110148,-0.059,0.041,-0.065417,9.941917
missing_mask_bits=0111011101110111011101110111011101111111111101111111111111111111
observed_counts_compact=rle:1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*11,1*1,0*19
[M6] rank=6 service=ts-seat-service metric=hubble_http_request_duration_p95_seconds baseline=0.052002 peak=5.048333 signed_z=164.263 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.025032,-0.007835,-0.000094,0.014672,0.039207,0.019385,0.002133,-0.021436,-0.044189,5.021458
missing_mask_bits=1101110111011101110111011101110111111111111111011111111111011111
observed_counts_compact=rle:0*2,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*15,1*1,0*11,1*1,0*5
[M7] rank=7 service=ts-travel-plan-service metric=hubble_http_request_duration_p99_seconds baseline=0.128177 peak=10.0 signed_z=105.809 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.097,-0.072223,0.290223,-0.269063,0.053108,0.000205,0.14625,-0.146591,-0.001909,9.903
missing_mask_bits=1011101110111011101110111011101110111111111111111011111111111111
observed_counts_compact=rle:0*1,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*15,1*1,0*14
[M8] rank=8 service=mysql metric=container.memory.working_set baseline=319386035.744681 peak=320016384.0 signed_z=17.761 onset_bin=33 onset_rel_s=249.853 persistence_bins=12
values_compact=delta:319270912,65536,0,0,14336,14336,0,8192,0,24576,-6144,-6144,0,20480,0,0,0,-6144,-6144,0,0,0,0,8192,0,0,0,24576,0,-2048,-2048,28672,0,565248,0,-552960,0,8192,8192,0,0,4096,0,0,0,0,262144,-114688,-114688,0,0,0,0,0,4096,0,-36864,0,-8192,0,0,0,0,-4096
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M9] rank=9 service=mysql metric=container.memory.usage baseline=533433409.361702 peak=534061056.0 signed_z=16.486 onset_bin=33 onset_rel_s=249.853 persistence_bins=12
values_compact=delta:533315584,57344,2048,2048,14336,14336,0,16384,0,20480,0,0,0,12288,0,0,0,-6144,-6144,0,0,0,0,8192,0,0,0,24576,0,-2048,-2048,28672,0,561152,0,-552960,0,8192,8192,0,0,4096,0,0,0,0,262144,-114688,-114688,0,0,0,0,0,4096,0,-36864,0,-8192,0,0,0,0,-4096
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M10] rank=10 service=loadgenerator metric=container.filesystem.available baseline=40178674056.17021 peak=39898787840.0 signed_z=-16.349 onset_bin=48 onset_rel_s=361.727 persistence_bins=16
values_compact=delta:40199493632,-587776,-1437696,-10022912,-808960,-808960,-1687552,-18374656,-925696,-925696,-2011136,-2048000,20178944,20178944,25362432,-36995072,-1021952,-1021952,-9580544,495616,-294912,-294912,-532480,0,-475136,-8929280,-253952,-253952,-622592,-17547264,-444416,-444416,-1032192,-1101824,20367360,20367360,-1273856,-9965568,-831488,-831488,-10190848,8253440,-862208,-862208,-1699840,6373376,-18683904,-18683904,-31555584,-17690624,0,-142684160,0,-24121344,-352256,-4454400,-4454400,-557056,-1486848,-4364288,-4364288,-593920,-561152,-335872
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M11] rank=11 service=ts-admin-basic-info-service metric=container.filesystem.available baseline=40178674056.17021 peak=39898787840.0 signed_z=-16.349 onset_bin=48 onset_rel_s=361.727 persistence_bins=16
values_compact=delta:40199493632,-587776,-1437696,-10022912,-808960,-808960,-1687552,-18374656,-925696,-925696,-2011136,-2048000,20178944,20178944,25362432,-36995072,-1021952,-1021952,-9580544,495616,-294912,-294912,-532480,0,-475136,-8929280,-253952,-253952,-622592,-17547264,-444416,-444416,-1032192,-1101824,20367360,20367360,-1273856,-9965568,-831488,-831488,-10190848,8253440,-862208,-862208,-1699840,6373376,-18683904,-18683904,-31555584,-17690624,0,-142684160,0,-24121344,-352256,-4454400,-4454400,-557056,-1486848,-4364288,-4364288,-593920,-561152,-335872
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M12] rank=12 service=ts-admin-order-service metric=container.filesystem.available baseline=40178674056.17021 peak=39898787840.0 signed_z=-16.349 onset_bin=48 onset_rel_s=361.727 persistence_bins=16
values_compact=delta:40199493632,-587776,-1437696,-10022912,-808960,-808960,-1687552,-18374656,-925696,-925696,-2011136,-2048000,20178944,20178944,25362432,-36995072,-1021952,-1021952,-9580544,495616,-294912,-294912,-532480,0,-475136,-8929280,-253952,-253952,-622592,-17547264,-444416,-444416,-1032192,-1101824,20367360,20367360,-1273856,-9965568,-831488,-831488,-10190848,8253440,-862208,-862208,-1699840,6373376,-18683904,-18683904,-31555584,-17690624,0,-142684160,0,-24121344,-352256,-4454400,-4454400,-557056,-1486848,-4364288,-4364288,-593920,-561152,-335872
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,1,2,1,2,1,2,1,2,1,2,1,2

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[249.68788766860962,459.6878876686096]

=== LOG SUMMARY ===
{"entries":[{"error_logs":3686,"error_pct":100.0,"service":"ts-ui-dashboard","total_logs":3686},{"error_logs":188,"error_pct":17.06,"service":"ts-food-service","total_logs":1102},{"error_logs":96,"error_pct":25.0,"service":"ts-delivery-service","total_logs":384},{"error_logs":95,"error_pct":25.0,"service":"ts-notification-service","total_logs":380},{"error_logs":95,"error_pct":3.11,"service":"ts-order-other-service","total_logs":3051},{"error_logs":32,"error_pct":2.94,"service":"ts-preserve-service","total_logs":1088},{"error_logs":28,"error_pct":0.94,"service":"ts-order-service","total_logs":2975},{"error_logs":10,"error_pct":100.0,"service":"mysql","total_logs":10}],"mode":"errors","omitted_services":24,"service_count":32}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":443865.5,"error_pct":75.52,"p95_during_ms":30017.9703838,"p95_pre_ms":6.761329999999997,"service":"ts-order-other-service","spans":4640},{"delta_pct":101397.0,"error_pct":14.71,"p95_during_ms":60013.749177050006,"p95_pre_ms":59.12860569999985,"service":"ts-seat-service","spans":6326},{"delta_pct":95017.4,"error_pct":37.5,"p95_during_ms":60032.65615275,"p95_pre_ms":63.11426854999996,"service":"ts-security-service","spans":714},{"delta_pct":21842.7,"error_pct":20.0,"p95_during_ms":60120.1262186,"p95_pre_ms":273.9864154999997,"service":"ts-travel2-service","spans":2474},{"delta_pct":6729.6,"error_pct":46.15,"p95_during_ms":60025.3281326,"p95_pre_ms":878.89867,"service":"ts-preserve-service","spans":694},{"delta_pct":5130.8,"error_pct":0.0,"p95_during_ms":20001.677014,"p95_pre_ms":382.3826886999999,"service":"ts-ui-dashboard","spans":3686},{"delta_pct":5098.3,"error_pct":15.27,"p95_during_ms":20002.492408500002,"p95_pre_ms":384.79153765,"service":"loadgenerator","spans":3685},{"delta_pct":4794.7,"error_pct":27.27,"p95_during_ms":60081.7460842,"p95_pre_ms":1227.491330999999,"service":"ts-route-plan-service","spans":776}],"omitted_services":22,"service_count":30}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=35 omitted_edges=5
[{"evidence_source":"metric","onset_rel_s":246.6,"rank":1,"service":"mysql","severity_z":17.761},{"evidence_source":"trace","onset_rel_s":263.4,"rank":2,"service":"ts-seat-service","severity_z":250.486},{"evidence_source":"trace","onset_rel_s":263.4,"rank":3,"service":"ts-order-other-service","severity_z":4.944},{"evidence_source":"trace","onset_rel_s":263.4,"rank":4,"service":"ts-travel-plan-service","severity_z":24.419},{"evidence_source":"trace","onset_rel_s":263.4,"rank":5,"service":"ts-travel2-service","severity_z":93.13},{"evidence_source":"trace","onset_rel_s":263.4,"rank":6,"service":"ts-route-plan-service","severity_z":25.739},{"evidence_source":"trace","onset_rel_s":263.4,"rank":7,"service":"loadgenerator","severity_z":4.078},{"evidence_source":"metric","onset_rel_s":381.0,"rank":8,"service":"ts-admin-basic-info-service","severity_z":16.349},{"evidence_source":"metric","onset_rel_s":381.0,"rank":9,"service":"ts-admin-order-service","severity_z":16.349},{"evidence_source":"metric","onset_rel_s":381.0,"rank":10,"service":"ts-admin-travel-service","severity_z":16.349},{"evidence_source":"metric","onset_rel_s":381.0,"rank":11,"service":"ts-auth-service","severity_z":16.349},{"evidence_source":"metric","onset_rel_s":381.0,"rank":12,"service":"ts-basic-service","severity_z":16.349},{"evidence_source":"metric","onset_rel_s":381.0,"rank":13,"service":"ts-cancel-service","severity_z":16.349},{"evidence_source":"metric","onset_rel_s":381.0,"rank":14,"service":"ts-config-service","severity_z":16.349}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"ts-travel2-service","caller":"ts-route-plan-service"},{"callee":"ts-config-service","caller":"ts-seat-service"},{"callee":"ts-order-other-service","caller":"ts-seat-service"},{"callee":"ts-route-plan-service","caller":"ts-travel-plan-service"},{"callee":"ts-seat-service","caller":"ts-travel-plan-service"},{"callee":"ts-basic-service","caller":"ts-travel2-service"},{"callee":"ts-seat-service","caller":"ts-travel2-service"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

[excluded before optimizer]

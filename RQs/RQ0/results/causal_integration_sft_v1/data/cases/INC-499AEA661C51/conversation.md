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
opaque_id: INC-499AEA661C51
observation_window={"duration_rel_s":477.526,"source_metric_rows":974}
selection_summary={"candidate_count":103,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":997,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["loadgenerator","loadgenerator-6cc8d677b6-99p5w","mysql","mysql-0","rabbitmq","rabbitmq-0","ts-admin-basic-info-service","ts-admin-basic-info-service-5cc86cdd64-ksdqg","ts-admin-order-service","ts-admin-order-service-74ccdb866f-gzrqp","ts-admin-route-service","ts-admin-route-service-648b6dc6cb-qqccf","ts-admin-travel-service","ts-admin-travel-service-594d757c69-nnt6t","ts-admin-user-service","ts-admin-user-service-578dd99c6b-xkgl5","ts-assurance-service","ts-assurance-service-5f5d76d86-5rkbx","ts-auth-service","ts-auth-service-79597b797c-tttgg","ts-avatar-service","ts-avatar-service-6cc8c76bb5-l5697","ts-basic-service","ts-basic-service-58879bf4df-qm422","ts-cancel-service","ts-cancel-service-6c5b744cc-gbxrk","ts-config-service","ts-config-service-59c49c67f7-hg4tp","ts-consign-price-service","ts-consign-price-service-6d956db986-bp5z6","ts-consign-service","ts-consign-service-cb47df75d-4bwrm","ts-contacts-service","ts-contacts-service-5bd6f6d854-zz2z6","ts-delivery-service","ts-delivery-service-655ccb75c5-kzt5w","ts-execute-service","ts-execute-service-568c69c7b8-hd658","ts-food-delivery-service","ts-food-delivery-service-bf584dcf6-9dg7f","ts-food-service","ts-food-service-6577cbc5bc-d77gn","ts-gateway-service","ts-gateway-service-75bf968657-qq879","ts-inside-payment-service","ts-inside-payment-service-6954f7c664-7grqb","ts-news-service","ts-news-service-7869d45c45-rdhrr","ts-notification-service","ts-notification-service-764666799b-ctfl2","ts-order-other-service","ts-order-other-service-cd899d7bd-kd25r","ts-order-service","ts-order-service-7b574fd599-9hv9c","ts-payment-service","ts-payment-service-5946bfbc65-q68pc","ts-preserve-other-service","ts-preserve-other-service-7f4d78bb5b-2w5sx","ts-preserve-service","ts-preserve-service-b7646c4c9-m4sj4","ts-price-service","ts-price-service-6f5f897546-825rb","ts-rebook-service","ts-rebook-service-79ff49c795-ttj42","ts-route-plan-service","ts-route-plan-service-6c7ddb4bc6-846cn","ts-route-service","ts-route-service-ccdcbd5c8-2pkf7","ts-seat-service","ts-seat-service-5bd7d4d9c8-j4mff","ts-security-service","ts-security-service-867fcd9fbf-d55lk","ts-station-food-service","ts-station-food-service-5f77969d84-jlmws","ts-station-service","ts-station-service-84d4687875-brl5z","ts-ticket-office-service","ts-ticket-office-service-56c759976d-xbx7p","ts-train-food-service","ts-train-food-service-7bc5dc97bb-mwvz4","ts-train-service","ts-train-service-6ffb8fd6c7-q5hqn","ts-travel-plan-service","ts-travel-plan-service-58ff74775f-69pbm","ts-travel-service","ts-travel-service-7bf44775ff-pz6vv","ts-travel2-service","ts-travel2-service-69454954f-kbw8b","ts-ui-dashboard","ts-ui-dashboard-5b4ff6488d-gvjbm","ts-user-service","ts-user-service-cd75d85d8-btb9l","ts-verification-code-service","ts-verification-code-service-849875c8c6-hf65r","ts-voucher-service","ts-voucher-service-68944b48-v2mcn","ts-wait-order-service","ts-wait-order-service-865bcf54dc-zzdrt","worker2","worker3","worker4","worker5","worker6"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[3.731,11.192,18.653,26.115,33.576,41.037,48.499,55.96,63.421,70.883,78.344,85.805,93.267,100.728,108.19,115.651,123.112,130.574,138.035,145.496,152.958,160.419,167.88,175.342,182.803,190.264,197.726,205.187,212.648,220.11,227.571,235.032,242.494,249.955,257.416,264.878,272.339,279.8,287.262,294.723,302.184,309.646,317.107,324.569,332.03,339.491,346.953,354.414,361.875,369.337,376.798,384.259,391.721,399.182,406.643,414.105,421.566,429.027,436.489,443.95,451.411,458.873,466.334,473.795]
[M1] rank=1 service=ts-ui-dashboard metric=hubble_http_request_duration_p50_seconds baseline=0.01771 peak=3.75 signed_z=451.38 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.013068,0.008032,0.01265,-0.00875,-0.015086,-0.000735,0.000488,0.010333,0.01125,3.71875,-3.735312,-0.005477,0.007039,-0.00125,0.006667,0.028333
missing_mask_bits=1011101110111011101110111011101110111011101110111011101110111011
observed_counts_compact=csv:0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0
[M2] rank=2 service=ts-travel-plan-service metric=k8s.pod.filesystem.usage baseline=609868.255319 peak=10690560.0 signed_z=317.589 onset_bin=32 onset_rel_s=242.494 persistence_bins=32
values_compact=delta:561152,4096,4096,4096,4096,4096,2048,2048,0,0,4096,0,4096,0,6144,6144,0,0,6144,10240,0,4096,6144,6144,2048,6144,6144,6144,2048,2048,4096,4096,131072,335872,534528,260096,487424,421888,233472,12288,2048,346112,493568,473088,0,208896,587776,448512,309248,571392,516096,176128,174080,583680,589824,172032,0,311296,380928,448512,120832,0,139264,376832
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,1,2,1,2,1,2
[M3] rank=3 service=ts-config-service metric=hubble_http_request_duration_p99_seconds baseline=0.022664 peak=4.65 signed_z=296.259 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.009904,0.013446,0.0249,-0.00075,-0.02385,-0.014383,0.0003,0.000255,4.640178,-4.6065,-0.0342,0.00055,-0.00035,0.000415,0.036335
missing_mask_bits=1011101110111011101110111011101110111111101110111011101110111011
observed_counts_compact=rle:0*1,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*7,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*2
[M4] rank=4 service=ts-user-service metric=hubble_http_request_duration_p90_seconds baseline=0.015576 peak=1.6 signed_z=168.191 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.018625,-0.009125,0.0065,0.0165,-0.005,-0.019964,-0.002586,0.00305,0.001333,1.590667,-1.59075,-0.00475,0.003,0.0015,-0.0005
missing_mask_bits=0111011101110111011101110111011101110111011101111111011101110111
observed_counts_compact=rle:1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*7,1*1,0*3,1*1,0*3,1*1,0*3
[M5] rank=5 service=ts-auth-service metric=hubble_http_request_duration_p99_seconds baseline=0.012171 peak=1.154975 signed_z=138.378 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.007448,0.000002,0.0189,0.00025,-0.019206,-0.000094,0.000081,0.000066,0.007378,1.14015,-1.147538,-0.000029,0.000027,0.007015,0.0003
missing_mask_bits=1011101110111011101110111011101110111111101110111011101110111011
observed_counts_compact=rle:0*1,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*7,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*2
[M6] rank=6 service=ts-price-service metric=container.cpu.usage baseline=0.026765 peak=0.697046 signed_z=87.221 onset_bin=40 onset_rel_s=302.184 persistence_bins=2
values_compact=delta:0.035561,0,-0.000885,-0.000884,-0.008277,-0.008277,0.010865,0.010865,-0.023171,0,0.009136,0,0.000486,0,0.001385,0.001384,0.009292,0,-0.001767,-0.001767,-0.003872,-0.003871,0,-0.011442,0,0,0.013271,0,-0.007225,0,0.000353,0,0.006684,0,-0.014681,0,-0.006665,0,-0.000099,0,0.690647,0,-0.685601,0,-0.005974,0,0.002342,0,-0.003513,0,0.002624,0,0.001739,0.001739,-0.003635,0,0.001918,0,-0.000439,-0.000439,-0.001169,0.005045,0.005045,-0.003692
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,1,2
[M7] rank=7 service=ts-price-service metric=k8s.pod.cpu.node.utilization baseline=0.000211 peak=0.004421 signed_z=69.156 onset_bin=39 onset_rel_s=294.723 persistence_bins=3
values_compact=delta:0.000252,0.00002,0,-0.000023,-0.000064,-0.000065,0,0.000149,0,0,-0.000094,0,0.000013,0,0.000039,0.000039,0.000006,0.000005,0.000025,0,-0.000089,0,-0.000082,0,-0.000013,0.000163,-0.000063,-0.000064,0,0.000032,0,0,-0.000035,0,-0.000014,0,-0.000042,-0.000041,0,0.004367,0,0,-0.004291,0,-0.000091,0.000039,0,0,-0.000046,0,0.00001,0.00001,0,0.000036,0,-0.000047,0.000026,0.000027,-0.000019,-0.000018,0,0.000009,0,0.00002
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,1,2
[M8] rank=8 service=ts-price-service metric=k8s.pod.cpu.usage baseline=0.027006 peak=0.565833 signed_z=69.156 onset_bin=39 onset_rel_s=294.723 persistence_bins=3
values_compact=delta:0.032291,0.002578,0,-0.002965,-0.008286,-0.008286,0,0.0191,0,0,-0.012092,0,0.001724,-0.000031,0.005021,0.005021,0.000712,0.000712,0.00313,0,-0.011332,0,-0.010471,0,-0.001721,0.020903,-0.008132,-0.008131,0,0.004037,0,0,-0.004398,0,-0.001891,0,-0.005308,-0.005308,0,0.558956,0,0,-0.549155,0,-0.01169,0.005037,0,0,-0.005889,0,0.001233,0.001233,0,0.004616,0,-0.005981,0.003389,0.00339,-0.002392,-0.002391,0,0.001279,0,0.002509
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,1,2
[M9] rank=9 service=ts-price-service metric=k8s.pod.cpu_limit_utilization baseline=0.005401 peak=0.113167 signed_z=69.156 onset_bin=39 onset_rel_s=294.723 persistence_bins=3
values_compact=delta:0.006458,0.000516,0,-0.000593,-0.001657,-0.001658,0,0.00382,0,0,-0.002418,0,0.000345,-0.000006,0.001004,0.001004,0.000142,0.000143,0.000626,0,-0.002267,0,-0.002094,0,-0.000344,0.004181,-0.001627,-0.001626,0,0.000807,0,0,-0.000879,0,-0.000378,0,-0.001062,-0.001062,0,0.111792,0,0,-0.109831,0,-0.002338,0.001007,0,0,-0.001178,0,0.000247,0.000246,0,0.000924,0,-0.001197,0.000678,0.000678,-0.000478,-0.000478,0,0.000255,0,0.000502
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,1,2
[M10] rank=10 service=ts-order-other-service metric=hubble_http_request_duration_p99_seconds baseline=0.054039 peak=2.275 signed_z=29.975 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.016763,0.007487,0.097475,0.104275,-0.216056,-0.00253,0.008853,-0.006317,0.039467,-0.033442,-0.006037,0.007087,-0.00711,0.007479,2.257606
missing_mask_bits=1011101110111011101110111011101110111111101110111011101110111011
observed_counts_compact=rle:0*1,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*7,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*2
[M11] rank=11 service=ts-travel-plan-service metric=container.memory.page_faults baseline=128757.489362 peak=146383.0 signed_z=27.796 onset_bin=33 onset_rel_s=249.955 persistence_bins=31
values_compact=delta:127635,181,0,256,0,122,0,0,125,0,83,0,41.5,41.5,298,0,132,7,0,36,0,122,24,24,255,0,243,0,172,35,0,86,0,1740,0,2109,0,0,1990,0,229.5,229.5,0,3198,0,1740,0,0,1355,58,0,0,74,0,1398,1398,0,22,22,35,35,386,386,29.5
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,1,2,1,2,1,2
[M12] rank=12 service=ts-travel-plan-service metric=k8s.pod.memory.page_faults baseline=129422.680851 peak=147033.0 signed_z=27.528 onset_bin=32 onset_rel_s=242.494 persistence_bins=32
values_compact=delta:128286.5,183.5,0,276,0,125,0,0,124,0,32,0,126,0,188,188,33.5,33.5,15,15,51,0,63.5,63.5,288,0,210,0,96,96,40,40,1150,0,1298,1298,438,0,1636,0,472,0,1706,0,1621,0,1659,0,1339,54,0,56,0,1030,894,894,0,24.5,24.5,32.5,32.5,767,0,33
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,1,2,1,2,1,2

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[305.40309166908264,475.45047092437744]

=== LOG SUMMARY ===
{"entries":[{"error_logs":2354,"error_pct":100.0,"service":"ts-ui-dashboard","total_logs":2354},{"error_logs":593,"error_pct":36.65,"service":"ts-travel-plan-service","total_logs":1618},{"error_logs":122,"error_pct":17.04,"service":"ts-food-service","total_logs":716},{"error_logs":96,"error_pct":25.0,"service":"ts-notification-service","total_logs":384},{"error_logs":95,"error_pct":25.0,"service":"ts-delivery-service","total_logs":380},{"error_logs":12,"error_pct":0.59,"service":"ts-order-service","total_logs":2022},{"error_logs":12,"error_pct":1.55,"service":"ts-preserve-service","total_logs":774}],"mode":"errors","omitted_services":23,"service_count":30}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":723.7,"error_pct":5.45,"p95_during_ms":3548.558807799999,"p95_pre_ms":430.8085356499996,"service":"ts-ui-dashboard","spans":2353},{"delta_pct":-98.6,"error_pct":71.7,"p95_during_ms":14.905609,"p95_pre_ms":1098.1349369,"service":"ts-travel-plan-service","spans":3128},{"delta_pct":70.7,"error_pct":0.0,"p95_during_ms":82.85691324999999,"p95_pre_ms":48.53531424999986,"service":"ts-consign-service","spans":384},{"delta_pct":62.1,"error_pct":0.0,"p95_during_ms":1002.6003549000001,"p95_pre_ms":618.5772451999987,"service":"ts-preserve-service","spans":481},{"delta_pct":54.7,"error_pct":0.0,"p95_during_ms":142.73659535000013,"p95_pre_ms":92.25070715,"service":"ts-food-service","spans":856},{"delta_pct":-46.2,"error_pct":0.0,"p95_during_ms":818.4751376,"p95_pre_ms":1521.7806938999997,"service":"ts-route-plan-service","spans":521},{"delta_pct":-41.4,"error_pct":0.0,"p95_during_ms":5.657734299999997,"p95_pre_ms":9.652176350000003,"service":"ts-config-service","spans":5255},{"delta_pct":-38.4,"error_pct":0.0,"p95_during_ms":11.68413629999997,"p95_pre_ms":18.9784935,"service":"ts-price-service","spans":1346}],"omitted_services":21,"service_count":29}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=35 omitted_edges=1
[{"evidence_source":"metric","onset_rel_s":249.0,"rank":1,"service":"ts-config-service","severity_z":296.259},{"evidence_source":"metric","onset_rel_s":271.2,"rank":2,"service":"ts-user-service","severity_z":168.191},{"evidence_source":"metric","onset_rel_s":275.4,"rank":3,"service":"loadgenerator","severity_z":17.792},{"evidence_source":"metric","onset_rel_s":275.4,"rank":4,"service":"ts-cancel-service","severity_z":17.792},{"evidence_source":"metric","onset_rel_s":275.4,"rank":5,"service":"ts-consign-service","severity_z":17.792},{"evidence_source":"metric","onset_rel_s":275.4,"rank":6,"service":"ts-notification-service","severity_z":17.792},{"evidence_source":"metric","onset_rel_s":275.4,"rank":7,"service":"ts-preserve-service","severity_z":17.792},{"evidence_source":"metric","onset_rel_s":275.4,"rank":8,"service":"ts-route-service","severity_z":17.792},{"evidence_source":"metric","onset_rel_s":279.6,"rank":9,"service":"ts-ui-dashboard","severity_z":451.38},{"evidence_source":"metric","onset_rel_s":300.0,"rank":10,"service":"ts-price-service","severity_z":87.221},{"evidence_source":"metric","onset_rel_s":309.0,"rank":11,"service":"ts-auth-service","severity_z":138.378},{"evidence_source":"metric","onset_rel_s":360.6,"rank":12,"service":"ts-travel-plan-service","severity_z":317.589},{"evidence_source":"trace","onset_rel_s":412.8,"rank":13,"service":"ts-food-service","severity_z":22.209},{"evidence_source":"metric","onset_rel_s":459.0,"rank":14,"service":"ts-order-other-service","severity_z":29.975}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"ts-ui-dashboard","caller":"loadgenerator"},{"callee":"ts-user-service","caller":"ts-cancel-service"},{"callee":"ts-food-service","caller":"ts-preserve-service"},{"callee":"ts-user-service","caller":"ts-preserve-service"},{"callee":"ts-auth-service","caller":"ts-ui-dashboard"},{"callee":"ts-cancel-service","caller":"ts-ui-dashboard"},{"callee":"ts-consign-service","caller":"ts-ui-dashboard"},{"callee":"ts-food-service","caller":"ts-ui-dashboard"},{"callee":"ts-order-other-service","caller":"ts-ui-dashboard"},{"callee":"ts-preserve-service","caller":"ts-ui-dashboard"},{"callee":"ts-route-service","caller":"ts-ui-dashboard"},{"callee":"ts-travel-plan-service","caller":"ts-ui-dashboard"},{"callee":"ts-user-service","caller":"ts-ui-dashboard"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

[excluded before optimizer]

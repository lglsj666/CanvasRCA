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
opaque_id: INC-BF9753D8862C
observation_window={"duration_rel_s":476.38,"source_metric_rows":949}
selection_summary={"candidate_count":104,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":913,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["loadgenerator","loadgenerator-84c757f555-l99kz","mysql","mysql-0","rabbitmq","rabbitmq-0","ts-admin-basic-info-service","ts-admin-basic-info-service-579748f6fc-j8rfk","ts-admin-order-service","ts-admin-order-service-655fd7b7cb-flqt6","ts-admin-route-service","ts-admin-route-service-58bfb4cc97-mqx77","ts-admin-travel-service","ts-admin-travel-service-57f4669564-5qq4d","ts-admin-user-service","ts-admin-user-service-788fb9f775-tsqn8","ts-assurance-service","ts-assurance-service-858c47f787-59qkw","ts-auth-service","ts-auth-service-7f7b9f74b4-2rrnv","ts-avatar-service","ts-avatar-service-7859d9b6f8-rgbrm","ts-basic-service","ts-basic-service-6d57966576-wzlzr","ts-cancel-service","ts-cancel-service-5979858c6-qb7cm","ts-config-service","ts-config-service-795d7b9cc6-hcpx7","ts-consign-price-service","ts-consign-price-service-56db65bff9-qjkmj","ts-consign-service","ts-consign-service-7f98cd6b79-4xdq9","ts-contacts-service","ts-contacts-service-c67494dcf-gxrwp","ts-delivery-service","ts-delivery-service-fb75484cd-hlnhs","ts-execute-service","ts-execute-service-6d87555bd5-zn922","ts-food-delivery-service","ts-food-delivery-service-7c7dd959c-czsl7","ts-food-service","ts-food-service-74f7b88bfd-ms72s","ts-gateway-service","ts-gateway-service-98ffc48c6-mf6nr","ts-inside-payment-service","ts-inside-payment-service-6558cd9645-rjh4v","ts-news-service","ts-news-service-7869d45c45-dgxhp","ts-notification-service","ts-notification-service-b89747469-xpv8k","ts-order-other-service","ts-order-other-service-57b5486dcc-vvtlw","ts-order-service","ts-order-service-bcc5cc698-p27fg","ts-payment-service","ts-payment-service-9ff84b9b8-66rk6","ts-preserve-other-service","ts-preserve-other-service-7797845cfc-wf2rz","ts-preserve-service","ts-preserve-service-6d6b5f4cbb-jjgp7","ts-price-service","ts-price-service-c696df855-5sfxx","ts-rebook-service","ts-rebook-service-77567cc6bb-ptzkm","ts-route-plan-service","ts-route-plan-service-6f74db974f-kglgf","ts-route-service","ts-route-service-6dcf9c5ccf-rbspr","ts-seat-service","ts-seat-service-6d77945967-d5g2t","ts-security-service","ts-security-service-6945c7f648-ttwsw","ts-station-food-service","ts-station-food-service-86ccc7545-cz5k7","ts-station-service","ts-station-service-745fb4b4fd-tff6z","ts-ticket-office-service","ts-ticket-office-service-7d58848599-rwjg9","ts-train-food-service","ts-train-food-service-5f748fdf99-psm8t","ts-train-service","ts-train-service-786fb85d88-z2l54","ts-travel-plan-service","ts-travel-plan-service-f946cdc66-w8mf4","ts-travel-service","ts-travel-service-f48bb6c74-vw2l6","ts-travel2-service","ts-travel2-service-5dfc5d8c56-pktwc","ts-ui-dashboard","ts-ui-dashboard-bd467f7cf-95cwt","ts-user-service","ts-user-service-6cbf658657-6c9lh","ts-verification-code-service","ts-verification-code-service-779d78bd9-2mt4f","ts-voucher-service","ts-voucher-service-7bbb9f7895-srrcf","ts-wait-order-service","ts-wait-order-service-5875864b5d-qvsfm","worker1","worker2","worker3","worker4","worker5","worker6"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[3.722,11.165,18.609,26.052,33.495,40.939,48.382,55.826,63.269,70.713,78.156,85.6,93.043,100.486,107.93,115.373,122.817,130.26,137.704,145.147,152.59,160.034,167.477,174.921,182.364,189.808,197.251,204.695,212.138,219.581,227.025,234.468,241.912,249.355,256.799,264.242,271.685,279.129,286.572,294.016,301.459,308.903,316.346,323.79,331.233,338.676,346.12,353.563,361.007,368.45,375.894,383.337,390.78,398.224,405.667,413.111,420.554,427.998,435.441,442.885,450.328,457.771,465.215,472.658]
[M1] rank=1 service=rabbitmq metric=container.memory.rss baseline=152229461.333333 peak=154001408.0 signed_z=884.619 onset_bin=43 onset_rel_s=323.79 persistence_bins=21
values_compact=rle:152227840*19,152231936*24,152236032*17,154001408*1,153118720*1,152236032*2
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M2] rank=2 service=rabbitmq metric=k8s.pod.memory.available baseline=865102080.0 peak=864833536.0 signed_z=-132.162 onset_bin=44 onset_rel_s=331.233 persistence_bins=20
values_compact=rle:865103872*18,865099776*26,865095680*5,865091584*1,864833536*2,865071104*2,865095680*10
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M3] rank=3 service=rabbitmq metric=k8s.pod.memory.usage baseline=222881536.0 peak=223150080.0 signed_z=132.162 onset_bin=44 onset_rel_s=331.233 persistence_bins=20
values_compact=rle:222879744*18,222883840*26,222887936*5,222892032*1,223150080*2,222912512*2,222887936*10
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M4] rank=4 service=rabbitmq metric=k8s.pod.memory.working_set baseline=208639744.0 peak=208908288.0 signed_z=132.162 onset_bin=44 onset_rel_s=331.233 persistence_bins=20
values_compact=rle:208637952*18,208642048*26,208646144*5,208650240*1,208908288*2,208670720*2,208646144*10
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M5] rank=5 service=rabbitmq metric=k8s.pod.memory_limit_utilization baseline=0.207575 peak=0.207825 signed_z=132.162 onset_bin=44 onset_rel_s=331.233 persistence_bins=20
values_compact=rle:0.207573*18,0.207577*26,0.207581*5,0.207584*1,0.207825*2,0.207603*2,0.207581*10
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M6] rank=6 service=rabbitmq metric=k8s.pod.memory.node.utilization baseline=0.001651 peak=0.001653 signed_z=132.162 onset_bin=0 onset_rel_s=3.722 persistence_bins=64
values_compact=rle:0.001651*50,0.001653*2,0.001651*12
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M7] rank=7 service=rabbitmq metric=container.memory.available baseline=880637184.0 peak=877223936.0 signed_z=-54.124 onset_bin=15 onset_rel_s=115.373 persistence_bins=9
values_compact=rle:880656384*15,880394240*2,880656384*2,880652288*5,880623616*1,880652288*11,880599040*2,880652288*5,880648192*5,879861760*3,880648192*6,880517120*1,880386048*2,877223936*1,878936064*1,880648192*2
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M8] rank=8 service=rabbitmq metric=container.memory.usage baseline=193190656.0 peak=196603904.0 signed_z=54.124 onset_bin=15 onset_rel_s=115.373 persistence_bins=9
values_compact=rle:193171456*15,193433600*2,193171456*2,193175552*5,193204224*1,193175552*11,193228800*2,193175552*5,193179648*5,193966080*3,193179648*6,193310720*1,193441792*2,196603904*1,194891776*1,193179648*2
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M9] rank=9 service=rabbitmq metric=container.memory.working_set baseline=193104640.0 peak=196517888.0 signed_z=54.124 onset_bin=15 onset_rel_s=115.373 persistence_bins=9
values_compact=rle:193085440*15,193347584*2,193085440*2,193089536*5,193118208*1,193089536*11,193142784*2,193089536*5,193093632*5,193880064*3,193093632*6,193224704*1,193355776*2,196517888*1,194805760*1,193093632*2
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M10] rank=10 service=ts-delivery-service metric=k8s.pod.memory.node.utilization baseline=0.005285 peak=0.005297 signed_z=13.292 onset_bin=33 onset_rel_s=249.355 persistence_bins=31
values_compact=rle:0.005283*3,0.005284*2,0.005285*13,0.005286*13,0.005287*2,0.005288*1,0.005289*1,0.00529*2,0.005289*6,0.00529*5,0.005291*4,0.005293*2,0.005297*3,0.005293*1,0.005294*6
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M11] rank=11 service=ts-delivery-service metric=k8s.pod.memory_limit_utilization baseline=0.22155 peak=0.222064 signed_z=13.292 onset_bin=33 onset_rel_s=249.355 persistence_bins=31
values_compact=delta:0.221478,-0.000007,0,0.00004,0,0.000012,0,0,0.000014,0,0,0,0.000001,0.000001,0,0.000001,0.000001,0,0.000027,0.000028,0.000001,0,-0.000025,0,0.000007,0,0.000004,0.000004,0.000002,0.000003,0,0.000022,0,0.000056,0.000055,0.000006,0.000006,-0.000043,0,0.000006,0,0.000029,0,0.000007,0,0.00001,0.00001,0.000014,0.000014,0.00001,0.00001,0,0.000073,0,0.000187,0,0,-0.000192,0.000033,0,0.000001,0,0.000013,0
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M12] rank=12 service=ts-delivery-service metric=k8s.pod.memory.usage baseline=713662037.333333 peak=715317248.0 signed_z=13.292 onset_bin=33 onset_rel_s=249.355 persistence_bins=31
values_compact=delta:713431040,-22528,0,126976,0,40960,0,0,45056,0,0,0,2048,2048,2048,2048,4096,0,88064,88064,4096,0,-81920,0,24576,0,12288,12288,8192,8192,0,69632,0,180224,180224,18432,18432,-139264,0,20480,0,94208,0,20480,0,32768,32768,45056,45056,32768,32768,0,233472,0,602112,0,0,-618496,106496,0,4096,0,40960,0
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[446.01838994026184,461.00559091567993]

=== LOG SUMMARY ===
{"entries":[{"error_logs":2304,"error_pct":19.36,"service":"ts-seat-service","total_logs":11900},{"error_logs":267,"error_pct":17.46,"service":"ts-food-service","total_logs":1529},{"error_logs":96,"error_pct":25.0,"service":"ts-notification-service","total_logs":384},{"error_logs":95,"error_pct":25.0,"service":"ts-delivery-service","total_logs":380},{"error_logs":51,"error_pct":3.63,"service":"ts-preserve-service","total_logs":1405},{"error_logs":51,"error_pct":1.23,"service":"ts-order-service","total_logs":4134},{"error_logs":41,"error_pct":0.73,"service":"ts-ui-dashboard","total_logs":5605},{"error_logs":4,"error_pct":4.35,"service":"ts-inside-payment-service","total_logs":92}],"mode":"errors","omitted_services":23,"service_count":31}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":739.3,"error_pct":0.0,"p95_during_ms":2349.7335175,"p95_pre_ms":279.9718223999999,"service":"ts-ui-dashboard","spans":5585},{"delta_pct":737.0,"error_pct":7.69,"p95_during_ms":2350.652839,"p95_pre_ms":280.8541749999998,"service":"loadgenerator","spans":5585},{"delta_pct":-80.6,"error_pct":0.0,"p95_during_ms":11.429765,"p95_pre_ms":58.820511399999994,"service":"ts-food-service","spans":1640},{"delta_pct":-70.9,"error_pct":0.0,"p95_during_ms":4.2653276,"p95_pre_ms":14.65557279999999,"service":"ts-train-food-service","spans":1734},{"delta_pct":-60.5,"error_pct":0.0,"p95_during_ms":266.70296329999996,"p95_pre_ms":674.7891050999991,"service":"ts-route-plan-service","spans":1222},{"delta_pct":-57.0,"error_pct":0.0,"p95_during_ms":4.62209605,"p95_pre_ms":10.740752799999987,"service":"ts-contacts-service","spans":2290},{"delta_pct":-56.2,"error_pct":0.0,"p95_during_ms":391.29870804999996,"p95_pre_ms":894.2051973999995,"service":"ts-travel-plan-service","spans":1629},{"delta_pct":-41.1,"error_pct":0.0,"p95_during_ms":3.7673101999999994,"p95_pre_ms":6.398855999999978,"service":"ts-order-service","spans":11132}],"omitted_services":22,"service_count":30}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=35 omitted_edges=0
[{"evidence_source":"metric","onset_rel_s":390.6,"rank":1,"service":"ts-delivery-service","severity_z":13.292},{"evidence_source":"metric","onset_rel_s":415.2,"rank":2,"service":"ts-avatar-service","severity_z":10.152},{"evidence_source":"metric","onset_rel_s":451.2,"rank":3,"service":"rabbitmq","severity_z":884.619},{"evidence_source":"none","onset_rel_s":null,"rank":4,"service":"ts-rebook-service","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":5,"service":"ts-station-service","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":6,"service":"ts-gateway-service","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":7,"service":"ts-execute-service","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":8,"service":"ts-travel-service","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":9,"service":"ts-admin-route-service","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":10,"service":"ts-admin-basic-info-service","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":11,"service":"ts-wait-order-service","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":12,"service":"ts-preserve-other-service","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":13,"service":"ts-route-plan-service","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":14,"service":"mysql","severity_z":0.0}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"ts-travel-service","caller":"ts-route-plan-service"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

[excluded before optimizer]

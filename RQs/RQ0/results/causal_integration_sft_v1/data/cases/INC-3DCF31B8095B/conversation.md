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
opaque_id: INC-3DCF31B8095B
observation_window={"duration_rel_s":478.94,"source_metric_rows":951}
selection_summary={"candidate_count":104,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":913,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["loadgenerator","loadgenerator-7c6465b994-twrgd","mysql","mysql-0","rabbitmq","rabbitmq-0","ts-admin-basic-info-service","ts-admin-basic-info-service-8498cf659d-25w9d","ts-admin-order-service","ts-admin-order-service-5f48c9847-ngq55","ts-admin-route-service","ts-admin-route-service-67f9bbcd98-6tkf8","ts-admin-travel-service","ts-admin-travel-service-7d676d8cf-6s8ln","ts-admin-user-service","ts-admin-user-service-5f875c8488-8jjsl","ts-assurance-service","ts-assurance-service-6b6f9549bd-wkcbw","ts-auth-service","ts-auth-service-54bd57586c-phpft","ts-avatar-service","ts-avatar-service-697c966bc9-tnnrd","ts-basic-service","ts-basic-service-599dcbcd59-6sf87","ts-cancel-service","ts-cancel-service-5d6f598b75-ddmhf","ts-config-service","ts-config-service-788886954c-pd2j5","ts-consign-price-service","ts-consign-price-service-65d465fbbd-6nkfl","ts-consign-service","ts-consign-service-f89c85c6-gjgm7","ts-contacts-service","ts-contacts-service-746b87fbc6-mm9zp","ts-delivery-service","ts-delivery-service-669dcd76fc-p7wp5","ts-execute-service","ts-execute-service-565f5cf898-w9sxj","ts-food-delivery-service","ts-food-delivery-service-6fcc5f49db-c8j74","ts-food-service","ts-food-service-5dd9757985-hq6p2","ts-gateway-service","ts-gateway-service-df699cb95-dh49m","ts-inside-payment-service","ts-inside-payment-service-69459cf8c4-8dmjk","ts-news-service","ts-news-service-6d6c6d7855-bnbw5","ts-notification-service","ts-notification-service-7967657c5d-7bhjz","ts-order-other-service","ts-order-other-service-86c75649c4-n9jv7","ts-order-service","ts-order-service-554d59f5c-mmsfl","ts-payment-service","ts-payment-service-66bfbd95f5-sr4zc","ts-preserve-other-service","ts-preserve-other-service-6bbdcb9df4-rt7zc","ts-preserve-service","ts-preserve-service-87fbbf5b5-bc5ln","ts-price-service","ts-price-service-54b6b4b96-wpm45","ts-rebook-service","ts-rebook-service-7f8fd67745-8wwpr","ts-route-plan-service","ts-route-plan-service-76fc6cc974-q5bv9","ts-route-service","ts-route-service-799f648896-rx5t7","ts-seat-service","ts-seat-service-675c89f44-lnrjb","ts-security-service","ts-security-service-6868bb5d87-kckkf","ts-station-food-service","ts-station-food-service-59fc9cbf74-96x7b","ts-station-service","ts-station-service-96ccf6fc-8gwv5","ts-ticket-office-service","ts-ticket-office-service-58c97df4b6-n7rgm","ts-train-food-service","ts-train-food-service-bcf66b6d8-clcdz","ts-train-service","ts-train-service-6bdbdb4547-zvzrv","ts-travel-plan-service","ts-travel-plan-service-5b7fb74b4f-cht2k","ts-travel-service","ts-travel-service-74794d67b9-5ctkm","ts-travel2-service","ts-travel2-service-6659b8fd5f-gldv9","ts-ui-dashboard","ts-ui-dashboard-59499f7b8b-5sbwl","ts-user-service","ts-user-service-87d8d9d54-2vcrl","ts-verification-code-service","ts-verification-code-service-6c9f97cb54-nn4d9","ts-voucher-service","ts-voucher-service-6f9ddf4fc4-q4h75","ts-wait-order-service","ts-wait-order-service-bbf549d5-97fvs","worker1","worker2","worker3","worker4","worker5","worker6"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[3.742,11.225,18.709,26.192,33.675,41.159,48.642,56.126,63.609,71.093,78.576,86.06,93.543,101.026,108.51,115.993,123.477,130.96,138.444,145.927,153.41,160.894,168.377,175.861,183.344,190.828,198.311,205.795,213.278,220.761,228.245,235.728,243.212,250.695,258.179,265.662,273.145,280.629,288.112,295.596,303.079,310.563,318.046,325.53,333.013,340.496,347.98,355.463,362.947,370.43,377.914,385.397,392.88,400.364,407.847,415.331,422.814,430.298,437.781,445.264,452.748,460.231,467.715,475.198]
[M1] rank=1 service=rabbitmq metric=container.memory.rss baseline=152901290.666667 peak=184111104.0 signed_z=999.0 onset_bin=51 onset_rel_s=385.397 persistence_bins=13
values_compact=rle:152895488*3,152899584*16,152901632*1,152903680*8,152907776*23,155105280*1,157302784*2,165568512*2,166936576*2,166948864*2,169816064*3,176963584*1
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M2] rank=2 service=rabbitmq metric=k8s.pod.memory.rss baseline=152938666.666667 peak=169852928.0 signed_z=999.0 onset_bin=52 onset_rel_s=392.88 persistence_bins=12
values_compact=rle:152932352*2,152936448*17,152938496*1,152940544*5,152942592*1,152944640*26,157339648*2,165605376*2,166973440*3,166985728*2,169852928*3
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M3] rank=3 service=ts-voucher-service metric=k8s.pod.memory.node.utilization baseline=0.000293 peak=0.000293 signed_z=999.0 onset_bin=0 onset_rel_s=3.742 persistence_bins=64
values_compact=rle:0.000293*64
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M4] rank=4 service=rabbitmq metric=container.memory.available baseline=879344896.0 peak=849350656.0 signed_z=-280.562 onset_bin=51 onset_rel_s=385.397 persistence_bins=13
values_compact=delta:879067136,331776,0,-8192,0,0,4096,0,0,0,0,0,0,0,-262144,0,262144,0,0,-143360,-143360,141312,141312,0,0,0,0,0,-4096,0,0,0,0,0,0,-4096,4096,0,0,-18432,-18432,32768,4096,0,0,0,-262144,0,262144,0,0,-2328576,-2328576,0,-8003584,0,-1368064,0,-274432,0,-1433600,0,0,-7149568
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M5] rank=5 service=rabbitmq metric=container.memory.usage baseline=194482944.0 peak=224477184.0 signed_z=280.562 onset_bin=51 onset_rel_s=385.397 persistence_bins=13
values_compact=delta:194760704,-331776,0,8192,0,0,-4096,0,0,0,0,0,0,0,262144,0,-262144,0,0,143360,143360,-141312,-141312,0,0,0,0,0,4096,0,0,0,0,0,0,4096,-4096,0,0,18432,18432,-32768,-4096,0,0,0,262144,0,-262144,0,0,2328576,2328576,0,8003584,0,1368064,0,274432,0,1433600,0,0,7149568
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M6] rank=6 service=rabbitmq metric=container.memory.working_set baseline=194396928.0 peak=224391168.0 signed_z=280.562 onset_bin=51 onset_rel_s=385.397 persistence_bins=13
values_compact=delta:194674688,-331776,0,8192,0,0,-4096,0,0,0,0,0,0,0,262144,0,-262144,0,0,143360,143360,-141312,-141312,0,0,0,0,0,4096,0,0,0,0,0,0,4096,-4096,0,0,18432,18432,-32768,-4096,0,0,0,262144,0,-262144,0,0,2328576,2328576,0,8003584,0,1368064,0,274432,0,1433600,0,0,7149568
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M7] rank=7 service=rabbitmq metric=k8s.pod.memory.available baseline=863811413.333333 peak=848084992.0 signed_z=-249.686 onset_bin=2 onset_rel_s=18.709 persistence_bins=17
values_compact=rle:863834112*2,863567872*2,863830016*15,863827968*1,863825920*5,863823872*1,863821824*9,863559680*2,863690752*1,863821824*1,863688704*1,863555584*1,863688704*1,863821824*10,859426816*2,850898944*2,849006592*3,849780736*2,848084992*3
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M8] rank=8 service=rabbitmq metric=k8s.pod.memory.usage baseline=224172202.666667 peak=239898624.0 signed_z=249.686 onset_bin=2 onset_rel_s=18.709 persistence_bins=17
values_compact=delta:224149504,0,266240,0,-262144,0,0,0,0,0,0,0,0,0,0,0,0,0,0,2048,2048,0,0,0,0,2048,2048,0,0,0,0,0,0,0,0,262144,0,-131072,-131072,133120,133120,-133120,-133120,0,0,0,0,0,0,0,0,0,4395008,0,8527872,0,1892352,0,0,-774144,0,1695744,0,0
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M9] rank=9 service=rabbitmq metric=k8s.pod.memory.working_set baseline=209930410.666667 peak=225656832.0 signed_z=249.686 onset_bin=2 onset_rel_s=18.709 persistence_bins=17
values_compact=delta:209907712,0,266240,0,-262144,0,0,0,0,0,0,0,0,0,0,0,0,0,0,2048,2048,0,0,0,0,2048,2048,0,0,0,0,0,0,0,0,262144,0,-131072,-131072,133120,133120,-133120,-133120,0,0,0,0,0,0,0,0,0,4395008,0,8527872,0,1892352,0,0,-774144,0,1695744,0,0
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M10] rank=10 service=rabbitmq metric=k8s.pod.memory_limit_utilization baseline=0.208777 peak=0.223423 signed_z=249.686 onset_bin=2 onset_rel_s=18.709 persistence_bins=17
values_compact=rle:0.208755*2,0.209003*2,0.208759*15,0.208761*1,0.208763*5,0.208765*1,0.208767*9,0.209011*2,0.208889*1,0.208767*1,0.208891*1,0.209015*1,0.208891*1,0.208767*10,0.21286*2,0.220802*2,0.222565*3,0.221844*2,0.223423*3
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M11] rank=11 service=rabbitmq metric=k8s.pod.memory.node.utilization baseline=0.00166 peak=0.001777 signed_z=249.686 onset_bin=2 onset_rel_s=18.709 persistence_bins=17
values_compact=rle:0.00166*2,0.001662*2,0.00166*31,0.001662*2,0.001661*1,0.00166*1,0.001661*1,0.001662*1,0.001661*1,0.00166*10,0.001693*2,0.001756*2,0.00177*3,0.001764*2,0.001777*3
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M12] rank=12 service=ts-food-service metric=k8s.pod.cpu_limit_utilization baseline=0.012903 peak=0.240106 signed_z=19.73 onset_bin=32 onset_rel_s=243.212 persistence_bins=2
values_compact=delta:0.009224,0.002939,0,0,-0.007322,0,0.039114,0,-0.036458,0,0.000267,0.000268,-0.003806,0,0.002325,0,0.012392,0.012392,-0.008644,-0.008644,-0.003501,-0.003501,0.000204,0.02442,0,-0.02404,-0.000513,-0.000512,0,0.000011,-0.001739,-0.001739,0.236969,0,-0.238392,0,-0.000018,0,-0.00068,0,0.001892,-0.001779,-0.000028,-0.000027,0.000596,0.000596,0,-0.000968,0,-0.000095,0,0,0.001474,0,-0.000244,-0.000244,-0.000439,-0.000438,0,0.000418,-0.000111,-0.000112,-0.000582,0
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[387.36636543273926,477.3376853466034]

=== LOG SUMMARY ===
{"entries":[{"error_logs":2864,"error_pct":19.35,"service":"ts-seat-service","total_logs":14800},{"error_logs":336,"error_pct":17.16,"service":"ts-food-service","total_logs":1958},{"error_logs":99,"error_pct":5.53,"service":"ts-preserve-service","total_logs":1791},{"error_logs":96,"error_pct":25.0,"service":"ts-notification-service","total_logs":384},{"error_logs":95,"error_pct":25.0,"service":"ts-delivery-service","total_logs":380},{"error_logs":89,"error_pct":1.78,"service":"ts-order-service","total_logs":5012},{"error_logs":2,"error_pct":3.23,"service":"ts-inside-payment-service","total_logs":62},{"error_logs":1,"error_pct":3.57,"service":"ts-payment-service","total_logs":28}],"mode":"errors","omitted_services":23,"service_count":31}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":2286.4,"error_pct":0.0,"p95_during_ms":32614.572193,"p95_pre_ms":1366.6719428999995,"service":"ts-preserve-service","spans":1149},{"delta_pct":347.7,"error_pct":0.0,"p95_during_ms":16.400578500000005,"p95_pre_ms":3.6636841999999987,"service":"ts-station-service","spans":7120},{"delta_pct":324.0,"error_pct":0.0,"p95_during_ms":21.78087519999999,"p95_pre_ms":5.137513199999999,"service":"ts-price-service","spans":4050},{"delta_pct":175.9,"error_pct":0.0,"p95_during_ms":12.168337800000002,"p95_pre_ms":4.411024649999998,"service":"ts-order-service","spans":13359},{"delta_pct":174.5,"error_pct":0.0,"p95_during_ms":12.208999650000006,"p95_pre_ms":4.44852635,"service":"ts-user-service","spans":5530},{"delta_pct":58.7,"error_pct":0.0,"p95_during_ms":57.531493999999995,"p95_pre_ms":36.2574783,"service":"ts-basic-service","spans":6346},{"delta_pct":54.8,"error_pct":0.0,"p95_during_ms":854.1973177,"p95_pre_ms":551.89793715,"service":"ts-route-plan-service","spans":1489},{"delta_pct":50.8,"error_pct":0.0,"p95_during_ms":7.519535799999983,"p95_pre_ms":4.985721,"service":"ts-train-service","spans":9490}],"omitted_services":22,"service_count":30}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=35 omitted_edges=0
[{"evidence_source":"metric","onset_rel_s":240.0,"rank":1,"service":"ts-food-service","severity_z":19.73},{"evidence_source":"metric","onset_rel_s":255.6,"rank":2,"service":"ts-verification-code-service","severity_z":11.879},{"evidence_source":"metric","onset_rel_s":271.2,"rank":3,"service":"ts-gateway-service","severity_z":14.992},{"evidence_source":"metric","onset_rel_s":304.8,"rank":4,"service":"ts-notification-service","severity_z":13.076},{"evidence_source":"metric","onset_rel_s":345.6,"rank":5,"service":"ts-admin-travel-service","severity_z":11.397},{"evidence_source":"metric","onset_rel_s":345.6,"rank":6,"service":"ts-assurance-service","severity_z":11.397},{"evidence_source":"metric","onset_rel_s":345.6,"rank":7,"service":"ts-execute-service","severity_z":11.397},{"evidence_source":"metric","onset_rel_s":345.6,"rank":8,"service":"ts-food-delivery-service","severity_z":11.397},{"evidence_source":"trace","onset_rel_s":394.2,"rank":9,"service":"ts-price-service","severity_z":23.782},{"evidence_source":"trace","onset_rel_s":394.2,"rank":10,"service":"ts-order-service","severity_z":14.467},{"evidence_source":"metric","onset_rel_s":400.2,"rank":11,"service":"ts-avatar-service","severity_z":13.861},{"evidence_source":"metric","onset_rel_s":418.8,"rank":12,"service":"ts-voucher-service","severity_z":999.0},{"evidence_source":"trace","onset_rel_s":424.2,"rank":13,"service":"ts-config-service","severity_z":7.475},{"evidence_source":"metric","onset_rel_s":452.4,"rank":14,"service":"rabbitmq","severity_z":999.0}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

[excluded before optimizer]

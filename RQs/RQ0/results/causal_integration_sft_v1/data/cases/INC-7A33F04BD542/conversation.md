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
opaque_id: INC-7A33F04BD542
observation_window={"duration_rel_s":478.732,"source_metric_rows":1079}
selection_summary={"candidate_count":104,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":1017,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["loadgenerator","loadgenerator-8465b66847-pcjwc","mysql","mysql-0","rabbitmq","rabbitmq-0","ts-admin-basic-info-service","ts-admin-basic-info-service-c7f4d66f9-srzt4","ts-admin-order-service","ts-admin-order-service-8578fdc446-9xpjs","ts-admin-route-service","ts-admin-route-service-5d945db787-s8w4x","ts-admin-travel-service","ts-admin-travel-service-96cbcb44b-zbcg4","ts-admin-user-service","ts-admin-user-service-5d8d74d79c-c45d4","ts-assurance-service","ts-assurance-service-79876db68f-j2h7m","ts-auth-service","ts-auth-service-5dd97d5ccd-jzlmm","ts-avatar-service","ts-avatar-service-9b66c896d-6sz88","ts-basic-service","ts-basic-service-68f7cbd746-ldpjd","ts-cancel-service","ts-cancel-service-6cb859955d-lpxnv","ts-config-service","ts-config-service-7c55667486-tghzx","ts-consign-price-service","ts-consign-price-service-6cffbf7945-2w477","ts-consign-service","ts-consign-service-745946dd49-9lwmr","ts-contacts-service","ts-contacts-service-657d4cdfbf-7pqx8","ts-delivery-service","ts-delivery-service-6b488868b8-fgkt2","ts-execute-service","ts-execute-service-86d5f5db59-ws8k6","ts-food-delivery-service","ts-food-delivery-service-56447bd89f-pnhtb","ts-food-service","ts-food-service-5fd45cf66d-sgw8x","ts-gateway-service","ts-gateway-service-669b9cf6bb-9mknr","ts-inside-payment-service","ts-inside-payment-service-5548965b7f-tmslg","ts-news-service","ts-news-service-6d6c6d7855-2m9rv","ts-notification-service","ts-notification-service-5f7c7d45c9-7xjnb","ts-order-other-service","ts-order-other-service-68fb6fd887-zpwrm","ts-order-service","ts-order-service-56b9db98d8-pmpvz","ts-payment-service","ts-payment-service-7648bd9bcd-pkgz2","ts-preserve-other-service","ts-preserve-other-service-5748c886c9-wfrqg","ts-preserve-service","ts-preserve-service-7684df89bd-8xpdn","ts-price-service","ts-price-service-7494fb49fc-pssnt","ts-rebook-service","ts-rebook-service-546f7bdbbd-lrk72","ts-route-plan-service","ts-route-plan-service-d9557d6d7-sbw6c","ts-route-service","ts-route-service-86dcd6b94f-dmxkj","ts-seat-service","ts-seat-service-75676c6d97-59njr","ts-security-service","ts-security-service-7cddbd789d-zlhlr","ts-station-food-service","ts-station-food-service-8c666b479-pc2c5","ts-station-service","ts-station-service-7ff47b8db8-w666m","ts-ticket-office-service","ts-ticket-office-service-5c75d795c-9mcc2","ts-train-food-service","ts-train-food-service-7b67f6b66f-xz4hg","ts-train-service","ts-train-service-7b65db49f4-g9nkw","ts-travel-plan-service","ts-travel-plan-service-5b7bdc7c56-5xkj9","ts-travel-service","ts-travel-service-7f856dcb7b-nktsc","ts-travel2-service","ts-travel2-service-79fb6f545d-ssqn2","ts-ui-dashboard","ts-ui-dashboard-64f6f55bb5-nccps","ts-user-service","ts-user-service-58c56cb98c-85gxb","ts-verification-code-service","ts-verification-code-service-57cddfb855-kr4cp","ts-voucher-service","ts-voucher-service-6b7fbfc649-zd54r","ts-wait-order-service","ts-wait-order-service-74df69f44-cxdn2","worker1","worker2","worker3","worker4","worker5","worker6"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[3.74,11.22,18.7,26.181,33.661,41.141,48.621,56.101,63.582,71.062,78.542,86.022,93.502,100.982,108.463,115.943,123.423,130.903,138.383,145.864,153.344,160.824,168.304,175.784,183.264,190.745,198.225,205.705,213.185,220.665,228.146,235.626,243.106,250.586,258.066,265.546,273.027,280.507,287.987,295.467,302.947,310.428,317.908,325.388,332.868,340.348,347.828,355.309,362.789,370.269,377.749,385.229,392.71,400.19,407.67,415.15,422.63,430.11,437.591,445.071,452.551,460.031,467.511,474.992]
[M1] rank=1 service=ts-ui-dashboard metric=hubble_http_request_duration_p50_seconds baseline=0.014683 peak=7.5 signed_z=558.17 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.05,-0.037115,-0.003746,0.000255,-0.001087,0.000582,0.000589,-0.000103,7.490625,-7.49,-0.001964,7.491964,-7.491719,0.000094,7.491625,-7.492625
missing_mask_bits=1101110111011101110111011101110111011101110111011101110111011101
observed_counts_compact=csv:0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0
[M2] rank=2 service=ts-basic-service metric=container.memory.rss baseline=732637952.0 peak=1978019840.0 signed_z=288.762 onset_bin=38 onset_rel_s=287.987 persistence_bins=26
values_compact=delta:730038272,0,8617984,-4933632,-4933632,3330048,3330048,0,-757760,0,-6713344,0,1286144,0,-2154496,0,278528,0,458752,18432,18432,4155392,4155392,208896,208896,81920,81920,0,139264,0,0,2686976,0,1380352,0,53248,53248,3516416,3516416,0,69632,10240,10240,18432,18432,0,1675264,0,67244032,0,201326592,0,252542976,0,0,213913600,0,218103808,0,167772160,107175936,0,0,16384
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M3] rank=3 service=ts-basic-service metric=container.memory.available baseline=2477632170.666667 peak=1229287424.0 signed_z=-282.978 onset_bin=38 onset_rel_s=287.987 persistence_bins=26
values_compact=delta:2480582656,0,-9412608,5335040,5335040,-3465216,-3465216,0,159744,0,7217152,0,-1019904,0,1679360,0,-24576,0,-712704,245760,245760,-4421632,-4421632,-75776,-75776,49152,49152,0,-946176,0,0,-1970176,0,-1638400,0,73728,73728,-3930112,-3930112,0,217088,247808,247808,-276480,-276480,0,-1146880,0,-67366912,0,-201707520,0,-253317120,0,0,-214052864,0,-218533888,0,-168103936,-108179456,0,0,503808
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M4] rank=4 service=ts-basic-service metric=container.memory.usage baseline=743978325.333333 peak=1992323072.0 signed_z=282.978 onset_bin=38 onset_rel_s=287.987 persistence_bins=26
values_compact=delta:741027840,0,9412608,-5335040,-5335040,3465216,3465216,0,-159744,0,-7217152,0,1019904,0,-1679360,0,24576,0,712704,-245760,-245760,4421632,4421632,75776,75776,-49152,-49152,0,946176,0,0,1970176,0,1638400,0,-73728,-73728,3930112,3930112,0,-217088,-247808,-247808,276480,276480,0,1146880,0,67366912,0,201707520,0,253317120,0,0,214052864,0,218533888,0,168103936,108179456,0,0,-503808
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M5] rank=5 service=ts-basic-service metric=container.memory.working_set baseline=743593301.333333 peak=1991938048.0 signed_z=282.978 onset_bin=38 onset_rel_s=287.987 persistence_bins=26
values_compact=delta:740642816,0,9412608,-5335040,-5335040,3465216,3465216,0,-159744,0,-7217152,0,1019904,0,-1679360,0,24576,0,712704,-245760,-245760,4421632,4421632,75776,75776,-49152,-49152,0,946176,0,0,1970176,0,1638400,0,-73728,-73728,3930112,3930112,0,-217088,-247808,-247808,276480,276480,0,1146880,0,67366912,0,201707520,0,253317120,0,0,214052864,0,218533888,0,168103936,108179456,0,0,-503808
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M6] rank=6 service=ts-basic-service metric=k8s.pod.memory.rss baseline=732448768.0 peak=1978056704.0 signed_z=275.542 onset_bin=37 onset_rel_s=280.507 persistence_bins=27
values_compact=delta:730079232,0,-1249280,0,0,11026432,0,-5136384,0,-3366912,-3366912,645120,645120,-1073152,-1073152,0,299008,67584,67584,180224,180224,4155392,4155392,372736,0,104448,104448,69632,69632,0,581632,1052672,1052672,1380352,0,53248,53248,7032832,0,30720,30720,28672,0,10240,10240,835584,835584,40960,0,100777984,0,260907008,0,211836928,140513280,0,0,228589568,0,176160768,109268992,8192,8192,0
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M7] rank=7 service=ts-basic-service metric=k8s.pod.memory.available baseline=2477055914.666667 peak=1228832768.0 signed_z=-265.25 onset_bin=37 onset_rel_s=280.507 persistence_bins=27
values_compact=delta:2479878144,0,1228800,0,0,-11030528,0,4222976,0,3360768,3360768,-217088,-217088,829440,829440,0,237568,-65536,-65536,-182272,-182272,-4161536,-4161536,-1355776,0,258048,258048,-581632,-581632,0,376832,-1198080,-1198080,-843776,0,-313344,-313344,-6565888,0,-141312,-141312,-40960,0,133120,133120,-837632,-837632,-577536,0,-101244928,0,-260866048,0,-212254720,-140824576,0,0,-229494784,0,-175742976,-109494272,-270336,-270336,0
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M8] rank=8 service=ts-basic-service metric=k8s.pod.memory.usage baseline=744554581.333333 peak=1992777728.0 signed_z=265.25 onset_bin=37 onset_rel_s=280.507 persistence_bins=27
values_compact=delta:741732352,0,-1228800,0,0,11030528,0,-4222976,0,-3360768,-3360768,217088,217088,-829440,-829440,0,-237568,65536,65536,182272,182272,4161536,4161536,1355776,0,-258048,-258048,581632,581632,0,-376832,1198080,1198080,843776,0,313344,313344,6565888,0,141312,141312,40960,0,-133120,-133120,837632,837632,577536,0,101244928,0,260866048,0,212254720,140824576,0,0,229494784,0,175742976,109494272,270336,270336,0
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M9] rank=9 service=ts-basic-service metric=k8s.pod.memory.working_set baseline=744169557.333333 peak=1992392704.0 signed_z=265.25 onset_bin=37 onset_rel_s=280.507 persistence_bins=27
values_compact=delta:741347328,0,-1228800,0,0,11030528,0,-4222976,0,-3360768,-3360768,217088,217088,-829440,-829440,0,-237568,65536,65536,182272,182272,4161536,4161536,1355776,0,-258048,-258048,581632,581632,0,-376832,1198080,1198080,843776,0,313344,313344,6565888,0,141312,141312,40960,0,-133120,-133120,837632,837632,577536,0,101244928,0,260866048,0,212254720,140824576,0,0,229494784,0,175742976,109494272,270336,270336,0
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M10] rank=10 service=ts-basic-service metric=k8s.pod.memory_limit_utilization baseline=0.23114 peak=0.61864 signed_z=265.25 onset_bin=37 onset_rel_s=280.507 persistence_bins=27
values_compact=delta:0.230264,0,-0.000381,0,0,0.003424,0,-0.001311,0,-0.001043,-0.001044,0.000068,0.000067,-0.000257,-0.000258,0,-0.000074,0.000021,0.00002,0.000057,0.000056,0.001292,0.001292,0.000421,0,-0.00008,-0.00008,0.00018,0.000181,0,-0.000117,0.000372,0.000372,0.000262,0,0.000097,0.000097,0.002038,0,0.000044,0.000044,0.000013,0,-0.000041,-0.000042,0.00026,0.00026,0.00018,0,0.03143,0,0.080984,0,0.065892,0.043718,0,0,0.071244,0,0.054558,0.033992,0.000084,0.000084,0
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M11] rank=11 service=ts-basic-service metric=k8s.pod.memory.node.utilization baseline=0.005514 peak=0.014758 signed_z=265.25 onset_bin=37 onset_rel_s=280.507 persistence_bins=27
values_compact=delta:0.005493,0,-0.000009,0,0,0.000082,0,-0.000032,0,-0.000024,-0.000025,0.000001,0.000002,-0.000006,-0.000006,0,-0.000002,0,0.000001,0.000001,0.000001,0.000031,0.000031,0.00001,0,-0.000002,-0.000002,0.000005,0.000004,0,-0.000003,0.000009,0.000009,0.000006,0,0.000002,0.000003,0.000048,0,0.000001,0.000001,0.000001,0,-0.000001,-0.000001,0.000006,0.000006,0.000005,0,0.000749,0,0.001932,0,0.001572,0.001043,0,0,0.0017,0,0.001301,0.000811,0.000002,0.000002,0
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M12] rank=12 service=ts-preserve-service metric=container.memory.available baseline=2496035157.333333 peak=1641095168.0 signed_z=-211.815 onset_bin=36 onset_rel_s=273.027 persistence_bins=28
values_compact=delta:2502975488,-1028096,-73728,0,-339968,0,-557056,0,-5566464,0,-700416,0,3895296,-339968,-339968,-944128,-944128,-1501184,-1501184,-172032,0,-176128,0,-20480,0,-90112,0,-851968,0,0,-315392,-2326528,0,-3092480,0,0,-37994496,0,10973184,0,-1689600,-1689600,-5185536,-5185536,-40960,0,4624384,4624384,-1626112,0,86016,86016,0,-225280,0,-1667072,-65460224,-65460224,-103292928,-103292928,-109365248,-109365248,-126873600,-126873600
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[387.9947860240936,477.9915134906769]

=== LOG SUMMARY ===
{"entries":[{"error_logs":6850,"error_pct":100.0,"service":"ts-ui-dashboard","total_logs":6850},{"error_logs":1064,"error_pct":9.11,"service":"ts-preserve-service","total_logs":11682},{"error_logs":981,"error_pct":3.79,"service":"ts-seat-service","total_logs":25862},{"error_logs":313,"error_pct":16.3,"service":"ts-food-service","total_logs":1920},{"error_logs":96,"error_pct":25.0,"service":"ts-delivery-service","total_logs":384},{"error_logs":95,"error_pct":25.0,"service":"ts-notification-service","total_logs":380},{"error_logs":80,"error_pct":0.77,"service":"ts-order-service","total_logs":10372}],"mode":"errors","omitted_services":24,"service_count":31}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":2635.0,"error_pct":5.73,"p95_during_ms":6461.333986999998,"p95_pre_ms":236.24211769999758,"service":"ts-ui-dashboard","spans":6849},{"delta_pct":220.2,"error_pct":0.0,"p95_during_ms":135.75182479999998,"p95_pre_ms":42.400046799999984,"service":"ts-food-service","spans":2067},{"delta_pct":-57.3,"error_pct":0.0,"p95_during_ms":3.56872225,"p95_pre_ms":8.35297875,"service":"ts-assurance-service","spans":792},{"delta_pct":-56.1,"error_pct":0.0,"p95_during_ms":7.014472399999998,"p95_pre_ms":15.980973549999943,"service":"ts-consign-service","spans":685},{"delta_pct":-42.4,"error_pct":0.0,"p95_during_ms":323.5194464,"p95_pre_ms":561.1991213000001,"service":"ts-route-plan-service","spans":1539},{"delta_pct":-34.8,"error_pct":0.0,"p95_during_ms":469.36675859999997,"p95_pre_ms":720.145729399999,"service":"ts-travel-plan-service","spans":2100},{"delta_pct":-25.7,"error_pct":0.0,"p95_during_ms":89.54291774999997,"p95_pre_ms":120.55407220000015,"service":"ts-travel2-service","spans":4808},{"delta_pct":-23.5,"error_pct":0.0,"p95_during_ms":3.0845787999999996,"p95_pre_ms":4.0315978999999995,"service":"ts-train-service","spans":19180}],"omitted_services":22,"service_count":30}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=35 omitted_edges=0
[{"evidence_source":"metric","onset_rel_s":249.6,"rank":1,"service":"ts-assurance-service","severity_z":14.376},{"evidence_source":"metric","onset_rel_s":256.8,"rank":2,"service":"ts-ui-dashboard","severity_z":558.17},{"evidence_source":"metric","onset_rel_s":258.0,"rank":3,"service":"ts-avatar-service","severity_z":11.271},{"evidence_source":"metric","onset_rel_s":275.4,"rank":4,"service":"ts-food-delivery-service","severity_z":204.067},{"evidence_source":"metric","onset_rel_s":337.2,"rank":5,"service":"ts-delivery-service","severity_z":11.238},{"evidence_source":"metric","onset_rel_s":342.0,"rank":6,"service":"ts-price-service","severity_z":12.868},{"evidence_source":"metric","onset_rel_s":343.8,"rank":7,"service":"ts-station-service","severity_z":11.893},{"evidence_source":"metric","onset_rel_s":352.2,"rank":8,"service":"ts-security-service","severity_z":27.179},{"evidence_source":"metric","onset_rel_s":360.6,"rank":9,"service":"ts-config-service","severity_z":16.393},{"evidence_source":"metric","onset_rel_s":360.6,"rank":10,"service":"ts-contacts-service","severity_z":11.655},{"evidence_source":"metric","onset_rel_s":367.8,"rank":11,"service":"ts-order-other-service","severity_z":19.57},{"evidence_source":"metric","onset_rel_s":412.8,"rank":12,"service":"ts-basic-service","severity_z":288.762},{"evidence_source":"trace","onset_rel_s":453.6,"rank":13,"service":"loadgenerator","severity_z":6.266},{"evidence_source":"metric","onset_rel_s":454.2,"rank":14,"service":"ts-preserve-service","severity_z":211.815}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"ts-ui-dashboard","caller":"loadgenerator"},{"callee":"ts-price-service","caller":"ts-basic-service"},{"callee":"ts-station-service","caller":"ts-basic-service"},{"callee":"ts-assurance-service","caller":"ts-preserve-service"},{"callee":"ts-basic-service","caller":"ts-preserve-service"},{"callee":"ts-contacts-service","caller":"ts-preserve-service"},{"callee":"ts-security-service","caller":"ts-preserve-service"},{"callee":"ts-order-other-service","caller":"ts-security-service"},{"callee":"ts-assurance-service","caller":"ts-ui-dashboard"},{"callee":"ts-contacts-service","caller":"ts-ui-dashboard"},{"callee":"ts-order-other-service","caller":"ts-ui-dashboard"},{"callee":"ts-preserve-service","caller":"ts-ui-dashboard"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

[excluded before optimizer]

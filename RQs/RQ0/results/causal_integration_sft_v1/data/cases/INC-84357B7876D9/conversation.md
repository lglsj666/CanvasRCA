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
opaque_id: INC-84357B7876D9
observation_window={"duration_rel_s":477.009,"source_metric_rows":1075}
selection_summary={"candidate_count":104,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":1024,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["loadgenerator","loadgenerator-794b57d884-7wz6l","mysql","mysql-0","rabbitmq","rabbitmq-0","ts-admin-basic-info-service","ts-admin-basic-info-service-8489f5b9dd-9sh7f","ts-admin-order-service","ts-admin-order-service-5b6c548fb5-zp76d","ts-admin-route-service","ts-admin-route-service-6b7fcc6f9b-2wt2j","ts-admin-travel-service","ts-admin-travel-service-7d4bb8dcb9-qdc2m","ts-admin-user-service","ts-admin-user-service-5bff4bdf86-nz6fv","ts-assurance-service","ts-assurance-service-5597965598-svrml","ts-auth-service","ts-auth-service-6d87cc4dc7-xf6vb","ts-avatar-service","ts-avatar-service-7c465d78b5-gc9lk","ts-basic-service","ts-basic-service-6968d4ccd5-k6dlt","ts-cancel-service","ts-cancel-service-6cf95f89fc-k8vpn","ts-config-service","ts-config-service-5d4b464d85-7zqf9","ts-consign-price-service","ts-consign-price-service-7d59bdd47d-f9lbw","ts-consign-service","ts-consign-service-848b6d5bcd-h86lr","ts-contacts-service","ts-contacts-service-55cfbdfdc8-dtgrm","ts-delivery-service","ts-delivery-service-d66597c7f-n4qqr","ts-execute-service","ts-execute-service-6687b7f74d-c8k5c","ts-food-delivery-service","ts-food-delivery-service-bcb844d44-gqzh4","ts-food-service","ts-food-service-55f49f6b59-7tv4h","ts-gateway-service","ts-gateway-service-7cc7b478fc-lgkd8","ts-inside-payment-service","ts-inside-payment-service-6d88d7f6b4-tnntw","ts-news-service","ts-news-service-6d6c6d7855-w8kp5","ts-notification-service","ts-notification-service-596b87f8f6-jdz2c","ts-order-other-service","ts-order-other-service-5fc6774cd8-z94k5","ts-order-service","ts-order-service-668587b48c-jnkkc","ts-payment-service","ts-payment-service-7679c6959c-tlrfm","ts-preserve-other-service","ts-preserve-other-service-6bf648d676-fqcsg","ts-preserve-service","ts-preserve-service-5d979f4b55-7kv76","ts-price-service","ts-price-service-55957b666-k6rt6","ts-rebook-service","ts-rebook-service-79d845d787-5k4sm","ts-route-plan-service","ts-route-plan-service-6865bfcc6d-wfcjx","ts-route-service","ts-route-service-586ffc746-k5jgx","ts-seat-service","ts-seat-service-7b7c5f5d7d-hl7lc","ts-security-service","ts-security-service-5454c847f7-qp6sc","ts-station-food-service","ts-station-food-service-cb9656f7b-gr8bb","ts-station-service","ts-station-service-685fd4985f-465x5","ts-ticket-office-service","ts-ticket-office-service-9c7b9d55b-ctqpp","ts-train-food-service","ts-train-food-service-bdd545d98-t2hlt","ts-train-service","ts-train-service-7b96f444bf-8w4v2","ts-travel-plan-service","ts-travel-plan-service-b49559b55-ng86d","ts-travel-service","ts-travel-service-56c9999f79-h9x6h","ts-travel2-service","ts-travel2-service-8557fd66df-p2m5l","ts-ui-dashboard","ts-ui-dashboard-68fff76764-vb5lj","ts-user-service","ts-user-service-644dc6f8fb-vdm7x","ts-verification-code-service","ts-verification-code-service-595bc8dd8d-bcwhk","ts-voucher-service","ts-voucher-service-c745bfccb-mtl8p","ts-wait-order-service","ts-wait-order-service-779f77459-xhgfn","worker1","worker2","worker3","worker4","worker5","worker6"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[3.727,11.18,18.633,26.086,33.54,40.993,48.446,55.9,63.353,70.806,78.259,85.713,93.166,100.619,108.072,115.526,122.979,130.432,137.885,145.339,152.792,160.245,167.699,175.152,182.605,190.058,197.512,204.965,212.418,219.871,227.325,234.778,242.231,249.685,257.138,264.591,272.044,279.498,286.951,294.404,301.857,309.311,316.764,324.217,331.67,339.124,346.577,354.03,361.484,368.937,376.39,383.843,391.297,398.75,406.203,413.656,421.11,428.563,436.016,443.47,450.923,458.376,465.829,473.283]
[M1] rank=1 service=ts-order-service-668587b48c-jnkkc metric=k8s.container.restarts baseline=0.0 peak=1.0 signed_z=999.0 onset_bin=38 onset_rel_s=286.951 persistence_bins=20
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010001000100010001000100100010001000100010001000100010001000100
observed_counts_compact=csv:1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1
[M2] rank=2 service=ts-order-service metric=container.filesystem.usage baseline=466944.0 peak=3080192.0 signed_z=848.404 onset_bin=32 onset_rel_s=242.231 persistence_bins=10
values_compact=rle:466944*32,1773568*1,3080192*3,34816*1,69632*1,442368*4,466944*22
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,2,1,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1
[M3] rank=3 service=ts-order-service metric=k8s.pod.memory.rss baseline=816452978.382979 peak=2838175744.0 signed_z=485.279 onset_bin=32 onset_rel_s=242.231 persistence_bins=28
values_compact=delta:814022656,0,0,110592,86016,0,4096,38912,38912,0,0,0,0,0,45056,0,0,0,2048,2048,0,65536,1032192,1032192,1376256,1376256,16384,16384,4071424,4071424,120832,120832,3346432,3346432,1001916416,1001916416,0,-2564530176,0,222912512,57124864,57124864,0,155271168,0,7614464,3399680,3399680,0,7442432,0,4067328,4388864,4388864,-4986880,-4986880,11083776,0,22134784,0,-21524480,0,6950912,0
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,2,1,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1
[M4] rank=4 service=ts-order-service metric=container.memory.rss baseline=816012876.255319 peak=2556997632.0 signed_z=461.825 onset_bin=30 onset_rel_s=227.325 persistence_bins=28
values_compact=delta:813981696,53248,53248,45056,45056,0,4096,38912,38912,0,0,0,0,0,22528,22528,0,0,2048,2048,32768,32768,403456,403456,1400832,0,2641920,0,299008,0,9740288,-1335296,0,0,1729069056,-2283393024,12685312,12685312,149587968,149587968,65132544,65132544,21098496,21098496,4919296,4919296,2506752,2506752,4399104,2097152,4382720,4382720,-10342400,10936320,1284096,1284096,6481920,6481920,-14467072,0,7020544,0
missing_mask_bits=0000000000000000000000000000000000011000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,2,1,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,0,0,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1
[M5] rank=5 service=ts-order-service metric=container.memory.available baseline=3467919882.893617 peak=1723830272.0 signed_z=-446.831 onset_bin=30 onset_rel_s=227.325 persistence_bins=28
values_compact=delta:3470127104,-47104,-47104,-184320,-184320,0,274432,-38912,-38912,-8192,0,0,0,-4096,-18432,-18432,-2048,-2048,-262144,-262144,94208,94208,-806912,-806912,-339968,0,-2641920,0,-557056,0,-10346496,1916928,0,0,-1732059136,2289721344,-13012992,-13012992,-154806272,-154806272,-69093376,-69093376,-13303808,-13303808,-4706304,-4706304,-3219456,-3219456,-4018176,-1085440,-4370432,-4370432,10117120,-10665984,-1527808,-1527808,-6631424,-6631424,14966784,0,-6742016,0
missing_mask_bits=0000000000000000000000000000000000011000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,2,1,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,0,0,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1
[M6] rank=6 service=ts-order-service metric=container.memory.working_set baseline=827047413.106383 peak=2571137024.0 signed_z=446.831 onset_bin=30 onset_rel_s=227.325 persistence_bins=30
values_compact=delta:824840192,47104,47104,184320,184320,0,-274432,38912,38912,8192,0,0,0,4096,18432,18432,2048,2048,262144,262144,-94208,-94208,806912,806912,339968,0,2641920,0,557056,0,10346496,-1916928,0,0,1732059136,-2562084864,238641152,33722368,13012992,13012992,154806272,154806272,69093376,69093376,13303808,13303808,4706304,4706304,3219456,3219456,4018176,1085440,4370432,4370432,-10117120,10665984,1527808,1527808,6631424,6631424,-14966784,0,6742016,0
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,2,1,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1
[M7] rank=7 service=ts-order-service metric=container.memory.usage baseline=827432437.106383 peak=2571489280.0 signed_z=446.823 onset_bin=30 onset_rel_s=227.325 persistence_bins=28
values_compact=delta:825225216,47104,47104,184320,184320,0,-274432,38912,38912,8192,0,0,0,4096,18432,18432,2048,2048,262144,262144,-94208,-94208,806912,806912,339968,0,2641920,0,557056,0,10346496,-1916928,0,0,1732026368,-2290040832,13189120,13189120,154806272,154806272,69093376,69093376,13303808,13303808,4706304,4706304,3219456,3219456,4018176,1085440,4370432,4370432,-10117120,10665984,1527808,1527808,6631424,6631424,-14966784,0,6742016,0
missing_mask_bits=0000000000000000000000000000000000011000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,2,1,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,0,0,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1
[M8] rank=8 service=ts-order-service metric=k8s.pod.memory.available baseline=3466705201.021276 peak=1440964608.0 signed_z=-441.322 onset_bin=32 onset_rel_s=242.231 persistence_bins=26
values_compact=delta:3469434880,0,0,-106496,-90112,0,-16384,-28672,-28672,0,-2048,-2048,0,0,-49152,0,4096,4096,-405504,-405504,0,471040,-1040384,-1040384,-1445888,-1445888,49152,49152,-5009408,-5009408,716800,716800,-3303424,-3303424,-1003874304,-1003874304,0,2571902976,0,-225804288,-57251840,-57251840,0,-158584832,0,-5554176,-2699264,-2699264,0,-8515584,0,-3022848,-4509696,-4509696,5017600,5017600,-11087872,0,-21901312,0,20238336,0,-5668864,0
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,2,1,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1
[M9] rank=9 service=ts-order-service metric=k8s.pod.memory.working_set baseline=828262094.978723 peak=2854002688.0 signed_z=441.322 onset_bin=32 onset_rel_s=242.231 persistence_bins=26
values_compact=delta:825532416,0,0,106496,90112,0,16384,28672,28672,0,2048,2048,0,0,49152,0,-4096,-4096,405504,405504,0,-471040,1040384,1040384,1445888,1445888,-49152,-49152,5009408,5009408,-716800,-716800,3303424,3303424,1003874304,1003874304,0,-2571902976,0,225804288,57251840,57251840,0,158584832,0,5554176,2699264,2699264,0,8515584,0,3022848,4509696,4509696,-5017600,-5017600,11087872,0,21901312,0,-20238336,0,5668864,0
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,2,1,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1
[M10] rank=10 service=ts-order-service metric=k8s.pod.memory.usage baseline=828647118.978723 peak=2854354944.0 signed_z=441.315 onset_bin=32 onset_rel_s=242.231 persistence_bins=26
values_compact=delta:825917440,0,0,106496,90112,0,16384,28672,28672,0,2048,2048,0,0,49152,0,-4096,-4096,405504,405504,0,-471040,1040384,1040384,1445888,1445888,-49152,-49152,5009408,5009408,-716800,-716800,3287040,3287040,1003874304,1003874304,0,-2572222464,0,226156544,57251840,57251840,0,158584832,0,5554176,2699264,2699264,0,8515584,0,3022848,4509696,4509696,-5017600,-5017600,11087872,0,21901312,0,-20238336,0,5668864,0
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,2,1,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1
[M11] rank=11 service=ts-order-service metric=k8s.pod.memory_limit_utilization baseline=0.192934 peak=0.664581 signed_z=441.315 onset_bin=32 onset_rel_s=242.231 persistence_bins=26
values_compact=delta:0.192299,0,0,0.000025,0.000021,0,0.000003,0.000007,0.000007,0,0,0.000001,0,0,0.000011,0,-0.000001,-0.000001,0.000095,0.000094,0,-0.00011,0.000243,0.000242,0.000337,0.000336,-0.000011,-0.000012,0.001167,0.001166,-0.000167,-0.000167,0.000766,0.000765,0.233733,0.233732,0,-0.598892,0,0.052656,0.01333,0.01333,0,0.036924,0,0.001293,0.000628,0.000629,0,0.001982,0,0.000704,0.00105,0.00105,-0.001168,-0.001168,0.002581,0,0.0051,0,-0.004712,0,0.001319,0
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,2,1,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1
[M12] rank=12 service=ts-order-service metric=k8s.pod.memory.node.utilization baseline=0.006137 peak=0.021139 signed_z=441.315 onset_bin=32 onset_rel_s=242.231 persistence_bins=26
values_compact=delta:0.006117,0,0,0,0.000001,0,0,0,0.000001,0,0,0,0,0,0,0,0,0,0.000003,0.000003,0,-0.000004,0.000008,0.000008,0.000011,0.00001,0,-0.000001,0.000038,0.000037,-0.000006,-0.000005,0.000024,0.000025,0.007434,0.007435,0,-0.01905,0,0.001675,0.000424,0.000424,0,0.001175,0,0.000041,0.00002,0.00002,0,0.000063,0,0.000022,0.000034,0.000033,-0.000037,-0.000037,0.000082,0,0.000162,0,-0.00015,0,0.000042,0
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,2,1,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[263.9257392883301,473.92635798454285]

=== LOG SUMMARY ===
{"entries":[{"error_logs":9544,"error_pct":100.0,"service":"ts-ui-dashboard","total_logs":9544},{"error_logs":410,"error_pct":16.17,"service":"ts-food-service","total_logs":2535},{"error_logs":195,"error_pct":2.55,"service":"ts-order-service","total_logs":7655},{"error_logs":191,"error_pct":7.15,"service":"ts-preserve-service","total_logs":2670},{"error_logs":96,"error_pct":25.0,"service":"ts-notification-service","total_logs":384},{"error_logs":95,"error_pct":25.0,"service":"ts-delivery-service","total_logs":380},{"error_logs":14,"error_pct":0.06,"service":"ts-seat-service","total_logs":21814},{"error_logs":10,"error_pct":100.0,"service":"mysql","total_logs":10}],"mode":"errors","omitted_services":24,"service_count":32}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":-74.7,"error_pct":0.0,"p95_during_ms":2.821168549999999,"p95_pre_ms":11.156238349999963,"service":"ts-config-service","spans":20910},{"delta_pct":-67.8,"error_pct":0.0,"p95_during_ms":34.2822098,"p95_pre_ms":106.5217695,"service":"ts-basic-service","spans":9354},{"delta_pct":-67.4,"error_pct":0.44,"p95_during_ms":17.10978079999999,"p95_pre_ms":52.46110019999996,"service":"ts-seat-service","spans":17420},{"delta_pct":-62.9,"error_pct":0.0,"p95_during_ms":334.55259394999973,"p95_pre_ms":900.572379,"service":"ts-preserve-service","spans":1759},{"delta_pct":-59.1,"error_pct":0.0,"p95_during_ms":5.6635995,"p95_pre_ms":13.8619725,"service":"ts-contacts-service","spans":4277},{"delta_pct":-56.8,"error_pct":0.0,"p95_during_ms":37.148685799999996,"p95_pre_ms":86.08052469999997,"service":"ts-food-service","spans":2489},{"delta_pct":-53.2,"error_pct":0.0,"p95_during_ms":417.6253970999998,"p95_pre_ms":892.68006575,"service":"ts-route-plan-service","spans":2264},{"delta_pct":-46.8,"error_pct":0.0,"p95_during_ms":87.96244145,"p95_pre_ms":165.33669419999998,"service":"ts-travel-service","spans":11569}],"omitted_services":22,"service_count":30}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=35 omitted_edges=1
[{"evidence_source":"metric","onset_rel_s":239.4,"rank":1,"service":"ts-travel-plan-service","severity_z":50.852},{"evidence_source":"trace","onset_rel_s":273.0,"rank":2,"service":"ts-seat-service","severity_z":14.662},{"evidence_source":"metric","onset_rel_s":274.2,"rank":3,"service":"ts-order-service","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":277.2,"rank":4,"service":"rabbitmq","severity_z":41.489},{"evidence_source":"metric","onset_rel_s":277.2,"rank":5,"service":"ts-admin-travel-service","severity_z":33.82},{"evidence_source":"metric","onset_rel_s":287.4,"rank":6,"service":"ts-auth-service","severity_z":41.165},{"evidence_source":"trace","onset_rel_s":293.4,"rank":7,"service":"ts-ui-dashboard","severity_z":5.609},{"evidence_source":"metric","onset_rel_s":316.8,"rank":8,"service":"mysql","severity_z":31.76},{"evidence_source":"metric","onset_rel_s":325.8,"rank":9,"service":"ts-cancel-service","severity_z":190.007},{"evidence_source":"metric","onset_rel_s":385.8,"rank":10,"service":"ts-preserve-service","severity_z":51.068},{"evidence_source":"metric","onset_rel_s":394.8,"rank":11,"service":"ts-news-service","severity_z":71.034},{"evidence_source":"metric","onset_rel_s":412.8,"rank":12,"service":"ts-route-plan-service","severity_z":52.498},{"evidence_source":"metric","onset_rel_s":441.6,"rank":13,"service":"ts-verification-code-service","severity_z":40.106},{"evidence_source":"metric","onset_rel_s":451.8,"rank":14,"service":"ts-train-food-service","severity_z":26.9}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"ts-verification-code-service","caller":"ts-auth-service"},{"callee":"ts-order-service","caller":"ts-cancel-service"},{"callee":"ts-order-service","caller":"ts-preserve-service"},{"callee":"ts-seat-service","caller":"ts-preserve-service"},{"callee":"ts-order-service","caller":"ts-seat-service"},{"callee":"ts-route-plan-service","caller":"ts-travel-plan-service"},{"callee":"ts-seat-service","caller":"ts-travel-plan-service"},{"callee":"ts-auth-service","caller":"ts-ui-dashboard"},{"callee":"ts-cancel-service","caller":"ts-ui-dashboard"},{"callee":"ts-order-service","caller":"ts-ui-dashboard"},{"callee":"ts-preserve-service","caller":"ts-ui-dashboard"},{"callee":"ts-travel-plan-service","caller":"ts-ui-dashboard"},{"callee":"ts-verification-code-service","caller":"ts-ui-dashboard"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

{"confidence":"high","reason":"Rank ts-order-service first because ts-order-service has direct k8s.container.restarts evidence (signed-z 999, persistence 20 bins); although ts-seat-service is salient, the caller path ts-seat-service -> ts-order-service means a disturbance in the callee can propagate back toward that caller-side symptom.","services":["ts-order-service","ts-seat-service"]}

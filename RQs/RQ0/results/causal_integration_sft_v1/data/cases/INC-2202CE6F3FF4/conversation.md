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
opaque_id: INC-2202CE6F3FF4
observation_window={"duration_rel_s":479.484,"source_metric_rows":1072}
selection_summary={"candidate_count":104,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":1008,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["loadgenerator","loadgenerator-77dc8db659-lcz2t","mysql","mysql-0","rabbitmq","rabbitmq-0","ts-admin-basic-info-service","ts-admin-basic-info-service-8489f5b9dd-s5wvw","ts-admin-order-service","ts-admin-order-service-5b6c548fb5-fdszn","ts-admin-route-service","ts-admin-route-service-6b7fcc6f9b-lxlgs","ts-admin-travel-service","ts-admin-travel-service-7d4bb8dcb9-gnv84","ts-admin-user-service","ts-admin-user-service-5bff4bdf86-pbvb6","ts-assurance-service","ts-assurance-service-5597965598-qn7xd","ts-auth-service","ts-auth-service-6d87cc4dc7-p5n47","ts-avatar-service","ts-avatar-service-7c465d78b5-7crxr","ts-basic-service","ts-basic-service-6968d4ccd5-9zmgr","ts-cancel-service","ts-cancel-service-6cf95f89fc-pw76c","ts-config-service","ts-config-service-5d4b464d85-mtdlt","ts-consign-price-service","ts-consign-price-service-7d59bdd47d-5kd4t","ts-consign-service","ts-consign-service-848b6d5bcd-th9wq","ts-contacts-service","ts-contacts-service-55cfbdfdc8-6jmj6","ts-delivery-service","ts-delivery-service-d66597c7f-2mh6f","ts-execute-service","ts-execute-service-6687b7f74d-cfjn6","ts-food-delivery-service","ts-food-delivery-service-bcb844d44-sgc6d","ts-food-service","ts-food-service-55f49f6b59-x74zn","ts-gateway-service","ts-gateway-service-7cc7b478fc-9jzdh","ts-inside-payment-service","ts-inside-payment-service-6d88d7f6b4-h9f6s","ts-news-service","ts-news-service-6d6c6d7855-nmrlx","ts-notification-service","ts-notification-service-596b87f8f6-jst8t","ts-order-other-service","ts-order-other-service-5fc6774cd8-b44mt","ts-order-service","ts-order-service-668587b48c-stxfv","ts-payment-service","ts-payment-service-7679c6959c-ccrlw","ts-preserve-other-service","ts-preserve-other-service-6bf648d676-v8p8n","ts-preserve-service","ts-preserve-service-5d979f4b55-phhqk","ts-price-service","ts-price-service-55957b666-bhdk6","ts-rebook-service","ts-rebook-service-79d845d787-jjszf","ts-route-plan-service","ts-route-plan-service-6865bfcc6d-gfqp6","ts-route-service","ts-route-service-586ffc746-xq5mr","ts-seat-service","ts-seat-service-7b7c5f5d7d-jcmt2","ts-security-service","ts-security-service-5454c847f7-cqwh5","ts-station-food-service","ts-station-food-service-cb9656f7b-z8rkk","ts-station-service","ts-station-service-685fd4985f-dr955","ts-ticket-office-service","ts-ticket-office-service-9c7b9d55b-jw6lf","ts-train-food-service","ts-train-food-service-bdd545d98-zl844","ts-train-service","ts-train-service-7b96f444bf-hk9r7","ts-travel-plan-service","ts-travel-plan-service-b49559b55-sjm9p","ts-travel-service","ts-travel-service-56c9999f79-v4wmw","ts-travel2-service","ts-travel2-service-8557fd66df-dc44j","ts-ui-dashboard","ts-ui-dashboard-68fff76764-jlfbb","ts-user-service","ts-user-service-644dc6f8fb-qxb9n","ts-verification-code-service","ts-verification-code-service-595bc8dd8d-2qzfb","ts-voucher-service","ts-voucher-service-c745bfccb-4jqrg","ts-wait-order-service","ts-wait-order-service-779f77459-kkjjf","worker1","worker2","worker3","worker4","worker5","worker6"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[3.746,11.238,18.73,26.222,33.714,41.206,48.698,56.19,63.682,71.173,78.665,86.157,93.649,101.141,108.633,116.125,123.617,131.109,138.601,146.093,153.585,161.077,168.569,176.061,183.553,191.045,198.536,206.028,213.52,221.012,228.504,235.996,243.488,250.98,258.472,265.964,273.456,280.948,288.44,295.932,303.424,310.916,318.408,325.9,333.391,340.883,348.375,355.867,363.359,370.851,378.343,385.835,393.327,400.819,408.311,415.803,423.295,430.787,438.279,445.771,453.263,460.754,468.246,475.738]
[M1] rank=1 service=ts-admin-travel-service metric=container.cpu.usage baseline=0.004933 peak=0.901062 signed_z=999.0 onset_bin=37 onset_rel_s=280.948 persistence_bins=27
values_compact=delta:0.004448,-0.000001,-0.000001,0,0.000468,0,0,0.000073,0,-0.000411,0,0.000255,0,0.000642,-0.000831,0,0,0,0,-0.000039,0,0.000579,0,-0.000428,-0.000429,0.00023,0.00023,0.000453,0.000454,0.000715,0,-0.000109,-0.000108,0.000277,0,0.00013,0,0.028857,0,0.865608,0,0,-0.810115,0,-0.082365,0,0.000729,-0.000968,-0.000967,0.000159,0.00016,0,-0.000504,0.000648,0.000648,-0.000108,-0.000109,0.000127,0.000126,-0.001224,0,0.000803,0,-0.000942
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M2] rank=2 service=ts-auth-service metric=hubble_http_request_duration_p90_seconds baseline=0.00464 peak=0.80225 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.0045,0.000141,-0.000141,0.00018,-0.00018,0,0.000051,0.000699,0.001375,0.000268,0.000107,0.006625,-0.000375,0.789,-0.7905
missing_mask_bits=0111011101110111011101110111011101110111111101110111011101110111
observed_counts_compact=rle:1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*7,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3
[M3] rank=3 service=ts-auth-service metric=hubble_http_request_duration_p95_seconds baseline=0.00514 peak=1.027375 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.00475,0.0005,-0.0005,0.000937,-0.000937,0,0.000054,0.001571,0.000688,0.000133,0.031429,-0.031375,0.007063,-0.000188,1.01325,-1.014
missing_mask_bits=0111011101110111011101110111011101110111011101110111011101110111
observed_counts_compact=csv:1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0
[M4] rank=4 service=ts-order-other-service metric=hubble_http_request_duration_p95_seconds baseline=0.008778 peak=1.0 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.008734,0.000141,-0.000375,0.000091,-0.000477,0.000021,0.001508,-0.000013,0.01037,0.43,0.55,-0.978,0.0455,-0.057786,-0.000097
missing_mask_bits=1101110111011101110111011101110111011111110111011101110111011101
observed_counts_compact=rle:0*2,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*7,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*1
[M5] rank=5 service=ts-order-service metric=hubble_http_request_duration_p90_seconds baseline=0.008594 peak=3.5 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.011685,-0.00348,0.00032,0.000339,-0.001129,0.000867,-0.000102,-0.001864,0.006595,0.005269,-0.001625,0.00275,3.480375,-3.480812
missing_mask_bits=0111011101110111011101110111011101110111111101110111111101110111
observed_counts_compact=rle:1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*7,1*1,0*3,1*1,0*7,1*1,0*3,1*1,0*3
[M6] rank=6 service=ts-order-service metric=hubble_http_request_duration_p95_seconds baseline=0.009661 peak=6.0 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.014592,-0.005414,0.000177,0.000077,-0.000417,0.000286,0.000045,-0.002278,0.008329,0.008853,-0.00225,0.062875,-0.060063,-0.010812,5.986,-5.977906
missing_mask_bits=0111011101110111011101110111011101110111011101110111011101110111
observed_counts_compact=csv:1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0
[M7] rank=7 service=ts-preserve-other-service metric=k8s.pod.cpu.node.utilization baseline=3.8e-05 peak=0.006979 signed_z=999.0 onset_bin=31 onset_rel_s=235.996 persistence_bins=29
values_compact=rle:0.000036*2,0.000037*1,0.000036*2,0.000038*2,0.000039*2,0.000032*2,0.000033*3,0.000043*2,0.000036*2,0.000035*2,0.000034*2,0.000043*2,0.000036*2,0.000042*5,0.000051*2,0.000047*2,0.000048*2,0.000135*1,0.006979*2,0.000143*3,0.000707*1,0.000057*1,0.000066*1,0.000075*1,0.00007*1,0.000066*1,0.000062*1,0.000059*1,0.000058*2,0.000064*1,0.000071*1,0.000058*2,0.000061*2,0.000057*2,0.000053*2,0.000056*1
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M8] rank=8 service=ts-preserve-other-service metric=k8s.pod.cpu.usage baseline=0.004838 peak=0.893264 signed_z=999.0 onset_bin=31 onset_rel_s=235.996 persistence_bins=29
values_compact=delta:0.004567,0.000078,0.000077,-0.000055,-0.000056,0.000317,0,0.000051,0,-0.00087,0,0.000085,0.000084,-0.000023,0.001259,0,-0.000885,0,-0.000134,0,-0.000189,0,0.001235,0,-0.000913,0,0.000768,0,0.000005,0,0,0.001089,0,-0.000413,0,0.000099,0,0.011162,0.875926,0,-0.874996,0,0,0.072235,-0.083245,0.001183,0.001184,-0.000609,-0.000609,-0.000436,-0.000436,-0.000062,-0.000061,0.000827,0.000827,-0.001591,0,0.000311,0,-0.000451,0,-0.000491,0,0.000369
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M9] rank=9 service=ts-preserve-other-service metric=k8s.pod.cpu_limit_utilization baseline=0.000968 peak=0.178653 signed_z=999.0 onset_bin=31 onset_rel_s=235.996 persistence_bins=29
values_compact=delta:0.000913,0.000016,0.000015,-0.000011,-0.000011,0.000064,0,0.00001,0,-0.000174,0,0.000017,0.000017,-0.000005,0.000252,0,-0.000177,0,-0.000027,0,-0.000038,0,0.000247,0,-0.000182,0,0.000153,0,0.000001,0,0,0.000218,0,-0.000083,0,0.00002,0,0.002233,0.175185,0,-0.174999,0,0,0.014447,-0.016649,0.000236,0.000237,-0.000122,-0.000122,-0.000087,-0.000087,-0.000012,-0.000013,0.000166,0.000165,-0.000318,0,0.000062,0,-0.00009,0,-0.000098,0,0.000074
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M10] rank=10 service=ts-route-service metric=hubble_http_request_duration_p95_seconds baseline=0.010328 peak=4.875 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.009701,0.000076,-0.000165,-0.000074,0.00042,-0.000319,0.000106,0.004905,0.00285,4.8575,-4.8325,0.0525,-0.04625,-0.0239,0.00015,-0.003188
missing_mask_bits=1101110111011101110111011101110111011101110111011101110111011101
observed_counts_compact=csv:0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0
[M11] rank=11 service=ts-seat-service metric=hubble_http_request_duration_p95_seconds baseline=0.02428 peak=0.205 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.02425,0,-0.000008,-0.000016,0.000293,-0.000269,0,0,0.019969,0.047031,-0.0075,0.01125,-0.01,-0.0425,0.1625,-0.18075
missing_mask_bits=0111011101110111011101110111011101110111011101110111011101110111
observed_counts_compact=csv:1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0
[M12] rank=12 service=ts-station-service metric=hubble_http_request_duration_p95_seconds baseline=0.008144 peak=1.375 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.009145,-0.000756,-0.000589,-0.001217,0.00235,-0.002433,0.002187,0.000427,0.000586,0.2253,-0.22525,-0.000083,1.365333,-1.354875,-0.010375,0.76525
missing_mask_bits=1101110111011101110111011101110111011101110111011101110111011101
observed_counts_compact=csv:0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[393.63093543052673,453.63093543052673]

=== LOG SUMMARY ===
{"entries":[{"error_logs":361,"error_pct":15.98,"service":"ts-food-service","total_logs":2259},{"error_logs":136,"error_pct":2.03,"service":"ts-order-service","total_logs":6684},{"error_logs":136,"error_pct":5.49,"service":"ts-preserve-service","total_logs":2479},{"error_logs":95,"error_pct":25.0,"service":"ts-notification-service","total_logs":380},{"error_logs":93,"error_pct":25.0,"service":"ts-delivery-service","total_logs":372},{"error_logs":2,"error_pct":0.02,"service":"ts-travel-service","total_logs":9182}],"mode":"errors","omitted_services":24,"service_count":30}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":11531.5,"error_pct":0.0,"p95_during_ms":5890.682452999999,"p95_pre_ms":50.64432909999996,"service":"ts-food-service","spans":2392},{"delta_pct":1599.8,"error_pct":0.0,"p95_during_ms":10926.91477725,"p95_pre_ms":642.8217618999997,"service":"ts-route-plan-service","spans":1863},{"delta_pct":1423.2,"error_pct":0.0,"p95_during_ms":11363.6162946,"p95_pre_ms":746.0586539000006,"service":"ts-travel-plan-service","spans":2472},{"delta_pct":1322.1,"error_pct":0.0,"p95_during_ms":2323.72739805,"p95_pre_ms":163.40276029999995,"service":"ts-travel-service","spans":9950},{"delta_pct":868.7,"error_pct":0.0,"p95_during_ms":2408.283980599993,"p95_pre_ms":248.5985145,"service":"ts-ui-dashboard","spans":7931},{"delta_pct":833.2,"error_pct":0.0,"p95_during_ms":2413.7465516999932,"p95_pre_ms":258.64101600000004,"service":"loadgenerator","spans":7931},{"delta_pct":141.1,"error_pct":0.0,"p95_during_ms":11.054664,"p95_pre_ms":4.584976199999994,"service":"ts-station-service","spans":9005},{"delta_pct":126.7,"error_pct":0.0,"p95_during_ms":1145.3506552000001,"p95_pre_ms":505.27387529999993,"service":"ts-preserve-service","spans":1605}],"omitted_services":22,"service_count":30}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=35 omitted_edges=3
[{"evidence_source":"metric","onset_rel_s":289.8,"rank":1,"service":"ts-preserve-other-service","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":291.0,"rank":2,"service":"ts-route-service","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":297.6,"rank":3,"service":"ts-admin-travel-service","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":306.0,"rank":4,"service":"ts-admin-user-service","severity_z":987.838},{"evidence_source":"metric","onset_rel_s":342.6,"rank":5,"service":"ts-travel-service","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":351.0,"rank":6,"service":"ts-order-other-service","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":381.0,"rank":7,"service":"ts-station-service","severity_z":999.0},{"evidence_source":"trace","onset_rel_s":394.8,"rank":8,"service":"ts-auth-service","severity_z":20.229},{"evidence_source":"metric","onset_rel_s":396.0,"rank":9,"service":"ts-basic-service","severity_z":767.924},{"evidence_source":"metric","onset_rel_s":423.6,"rank":10,"service":"ts-order-service","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":426.0,"rank":11,"service":"ts-seat-service","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":447.6,"rank":12,"service":"ts-food-service","severity_z":840.033},{"evidence_source":"trace","onset_rel_s":474.6,"rank":13,"service":"ts-ui-dashboard","severity_z":4.211},{"evidence_source":"trace","onset_rel_s":474.6,"rank":14,"service":"loadgenerator","severity_z":3.754}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"ts-ui-dashboard","caller":"loadgenerator"},{"callee":"ts-route-service","caller":"ts-basic-service"},{"callee":"ts-station-service","caller":"ts-basic-service"},{"callee":"ts-travel-service","caller":"ts-food-service"},{"callee":"ts-order-other-service","caller":"ts-seat-service"},{"callee":"ts-order-service","caller":"ts-seat-service"},{"callee":"ts-basic-service","caller":"ts-travel-service"},{"callee":"ts-route-service","caller":"ts-travel-service"},{"callee":"ts-seat-service","caller":"ts-travel-service"},{"callee":"ts-auth-service","caller":"ts-ui-dashboard"},{"callee":"ts-food-service","caller":"ts-ui-dashboard"},{"callee":"ts-order-other-service","caller":"ts-ui-dashboard"},{"callee":"ts-order-service","caller":"ts-ui-dashboard"},{"callee":"ts-route-service","caller":"ts-ui-dashboard"},{"callee":"ts-travel-service","caller":"ts-ui-dashboard"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

[excluded before optimizer]

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
opaque_id: INC-0DD3AD735CA2
observation_window={"duration_rel_s":475.396,"source_metric_rows":758}
selection_summary={"candidate_count":102,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":900,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["loadgenerator","loadgenerator-5867cb5967-dqg4l","mysql","mysql-0","rabbitmq","rabbitmq-0","ts-admin-basic-info-service","ts-admin-basic-info-service-6659d9d49-q8fpq","ts-admin-order-service","ts-admin-order-service-74874bb64-xz7nl","ts-admin-route-service","ts-admin-route-service-bfb45ff69-sp74r","ts-admin-travel-service","ts-admin-travel-service-685895dffb-66t56","ts-admin-user-service","ts-admin-user-service-7c45675555-krc68","ts-assurance-service","ts-assurance-service-76459f5575-6hx6h","ts-auth-service","ts-auth-service-5c98dd7948-vhqw8","ts-avatar-service","ts-avatar-service-868fb4bf7d-wms24","ts-basic-service","ts-basic-service-5cdf66d69b-6ksjt","ts-cancel-service","ts-cancel-service-55ccd7978d-nrn7c","ts-config-service","ts-config-service-b9bcfbc56-658jh","ts-consign-price-service","ts-consign-price-service-6749d49475-q5cf2","ts-consign-service","ts-consign-service-b74f9b59f-lq2ft","ts-contacts-service","ts-contacts-service-848bdcc799-2fgqv","ts-delivery-service","ts-delivery-service-6f79457966-d575w","ts-execute-service","ts-execute-service-5dbbc755fc-2b8w2","ts-food-delivery-service","ts-food-delivery-service-74ffc6dbb9-xd2tj","ts-food-service","ts-food-service-66b764476b-mvvdg","ts-gateway-service","ts-gateway-service-785597f976-msmgp","ts-inside-payment-service","ts-inside-payment-service-655f955977-qwd76","ts-news-service","ts-news-service-7869d45c45-vllc9","ts-notification-service","ts-notification-service-55b4f48c8f-mz559","ts-order-other-service","ts-order-other-service-677c8677b5-m8q56","ts-order-service","ts-order-service-5db685fb54-4svz5","ts-payment-service","ts-payment-service-58fff7fd68-zrtm6","ts-preserve-other-service","ts-preserve-other-service-745ffd9f57-hh8tq","ts-preserve-service","ts-preserve-service-79b467b6c8-nm6cw","ts-price-service","ts-price-service-fcbdb55f5-cf5dk","ts-rebook-service","ts-rebook-service-67f4f4986-47mtm","ts-route-plan-service","ts-route-plan-service-6b4859cf65-xk4n2","ts-route-service","ts-route-service-757558799f-64g2w","ts-seat-service","ts-seat-service-8959d487f-5qmnn","ts-security-service","ts-security-service-5fbb5c757b-jvcjf","ts-station-food-service","ts-station-food-service-864c57dbc7-g29hb","ts-station-service","ts-station-service-774c9cb8b-ndvqk","ts-ticket-office-service","ts-ticket-office-service-8687d77bc5-pjxnt","ts-train-food-service","ts-train-food-service-64c578fd99-j294z","ts-train-service","ts-train-service-7575645468-r8h7v","ts-travel-plan-service","ts-travel-plan-service-6c75975898-txk9s","ts-travel-service","ts-travel-service-765c9c9858-smnj9","ts-travel2-service","ts-travel2-service-5b97989896-4fp9g","ts-ui-dashboard","ts-ui-dashboard-69f886fc55-ffgrv","ts-user-service","ts-user-service-d5b9d4bb9-wnth6","ts-verification-code-service","ts-verification-code-service-57566595bf-khnmc","ts-voucher-service","ts-voucher-service-69d7fdccff-586zh","ts-wait-order-service","ts-wait-order-service-7c88777746-tqcx6","worker2","worker3","worker5","worker6"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[3.714,11.142,18.57,25.998,33.426,40.854,48.282,55.71,63.139,70.567,77.995,85.423,92.851,100.279,107.707,115.135,122.563,129.991,137.419,144.847,152.275,159.703,167.131,174.56,181.988,189.416,196.844,204.272,211.7,219.128,226.556,233.984,241.412,248.84,256.268,263.696,271.124,278.552,285.98,293.409,300.837,308.265,315.693,323.121,330.549,337.977,345.405,352.833,360.261,367.689,375.117,382.545,389.973,397.401,404.829,412.258,419.686,427.114,434.542,441.97,449.398,456.826,464.254,471.682]
[M1] rank=1 service=ts-avatar-service metric=container.memory.page_faults baseline=49038.479167 peak=49658.0 signed_z=21.029 onset_bin=34 onset_rel_s=256.268 persistence_bins=30
values_compact=delta:49000,0,0,6,0,0,1,0,0,0,0,0,4,0,45,0,0,0,0,0,4,5,0,0,0,0,0,9,0,0,0,0,0,31,31,3,0,3,0,17,0,0,0,0.5,0.5,0,0,79,0,0,0,0,2,0,417,0,0,0,0,0,0,0,0,0
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M2] rank=2 service=rabbitmq metric=container.memory.rss baseline=151498490.553191 peak=151519232.0 signed_z=20.715 onset_bin=0 onset_rel_s=3.714 persistence_bins=30
values_compact=rle:151494656*2,151498752*34,151511040*8,151515136*8,151517184*1,151519232*11
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1
[M3] rank=3 service=ts-avatar-service metric=k8s.pod.memory.page_faults baseline=49832.9375 peak=50452.0 signed_z=20.594 onset_bin=34 onset_rel_s=256.268 persistence_bins=30
values_compact=delta:49784,10,0,0,7,0,0,0,0,0,0,0,4,45,0,0,0,0,0,0,4,5,0,0,0,0,0,9,0,0,0,0,0,31,31,0,3,1.5,1.5,17,0,0,0,0.5,0.5,38.5,38.5,0,2,0,0,0,2,208.5,208.5,0,0,0,0,0,0,0,0,0
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M4] rank=4 service=mysql metric=k8s.pod.memory.rss baseline=293365845.333333 peak=293670912.0 signed_z=18.596 onset_bin=38 onset_rel_s=285.98 persistence_bins=26
values_compact=delta:293330944,4096,0,4096,4096,0,8192,8192,8192,0,0,0,0,0,0,0,0,0,0,0,0,4096,0,2048,2048,0,0,0,0,10240,10240,2048,2048,0,12288,0,0,0,32768,32768,12288,0,20480,12288,0,0,57344,65536,0,0,0,0,0,0,0,0,8192,0,4096,4096,0,0,0,8192
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1
[M5] rank=5 service=mysql metric=container.memory.rss baseline=293325397.333333 peak=293629952.0 signed_z=17.556 onset_bin=36 onset_rel_s=271.124 persistence_bins=28
values_compact=delta:293289984,4096,0,8192,0,4096,4096,0,0,16384,0,0,0,0,0,0,0,0,0,0,0,2048,2048,2048,2048,0,0,0,20480,0,0,4096,0,0,0,12288,32768,32768,0,0,10240,10240,0,24576,0,53248,0,0,69632,0,0,0,0,0,0,0,8192,0,4096,4096,0,0,4096,4096
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1
[M6] rank=6 service=rabbitmq metric=k8s.pod.memory.rss baseline=151535180.255319 peak=151556096.0 signed_z=16.562 onset_bin=37 onset_rel_s=278.552 persistence_bins=27
values_compact=rle:151531520*3,151533568*1,151535616*33,151547904*7,151549952*1,151552000*7,151554048*1,151556096*11
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1
[M7] rank=7 service=ts-user-service metric=container.memory.available baseline=2428051029.333333 peak=2410463232.0 signed_z=-14.957 onset_bin=34 onset_rel_s=256.268 persistence_bins=30
values_compact=delta:2431676416,-2727936,0,0,-806912,0,708608,0,-28672,49152,0,0,-126976,0,-53248,0,-663552,0,-81920,0,-450560,-450560,-348160,0,77824,0,57344,57344,-94208,-192512,0,0,-1175552,0,-14086144,-2048,-2048,-137216,-137216,-8192,0,-4096,-4096,0,0,-163840,-163840,75776,75776,0,-278528,0,-36864,0,-90112,100352,100352,0,0,-16384,-16384,-8192,-8192,8192
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M8] rank=8 service=ts-user-service metric=container.memory.usage baseline=793559466.666667 peak=811147264.0 signed_z=14.957 onset_bin=34 onset_rel_s=256.268 persistence_bins=30
values_compact=delta:789934080,2727936,0,0,806912,0,-708608,0,28672,-49152,0,0,126976,0,53248,0,663552,0,81920,0,450560,450560,348160,0,-77824,0,-57344,-57344,94208,192512,0,0,1175552,0,14086144,2048,2048,137216,137216,8192,0,4096,4096,0,0,163840,163840,-75776,-75776,0,278528,0,36864,0,90112,-100352,-100352,0,0,16384,16384,8192,8192,-8192
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M9] rank=9 service=ts-user-service metric=container.memory.working_set baseline=793174442.666667 peak=810762240.0 signed_z=14.957 onset_bin=34 onset_rel_s=256.268 persistence_bins=30
values_compact=delta:789549056,2727936,0,0,806912,0,-708608,0,28672,-49152,0,0,126976,0,53248,0,663552,0,81920,0,450560,450560,348160,0,-77824,0,-57344,-57344,94208,192512,0,0,1175552,0,14086144,2048,2048,137216,137216,8192,0,4096,4096,0,0,163840,163840,-75776,-75776,0,278528,0,36864,0,90112,-100352,-100352,0,0,16384,16384,8192,8192,-8192
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M10] rank=10 service=ts-user-service metric=container.memory.page_faults baseline=160460.791667 peak=164843.0 signed_z=14.716 onset_bin=34 onset_rel_s=256.268 persistence_bins=30
values_compact=delta:159865,300,0,0,19,0,32,0,8,10,0,0,39,0,18,0,186,0,32,0,118,118,26,0,47,0,3,3,21,48,0,0,287,0,3446,0.5,0.5,34,34,7,0,2.5,2.5,1,0,21,21,5,5,0,10,0,9,0,29,6,6,0,0,7.5,7.5,1,1,6
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M11] rank=11 service=ts-user-service metric=container.memory.rss baseline=782329685.333333 peak=799809536.0 signed_z=14.132 onset_bin=34 onset_rel_s=256.268 persistence_bins=30
values_compact=delta:778297344,3215360,0,0,77824,0,20480,0,32768,-28672,0,0,106496,0,53248,0,659456,0,73728,0,452608,452608,77824,0,188416,0,-40960,-40960,86016,172032,0,0,1175552,0,14065664,2048,2048,137216,137216,8192,0,4096,4096,0,0,67584,67584,20480,20480,0,20480,0,32768,0,94208,24576,24576,0,0,18432,18432,4096,4096,0
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M12] rank=12 service=ts-user-service metric=k8s.pod.memory.page_faults baseline=161139.0625 peak=165529.0 signed_z=14.13 onset_bin=35 onset_rel_s=263.696 persistence_bins=29
values_compact=delta:160551,0,153.5,153.5,15.5,15.5,0,21,0,20,0,22,0,15,0,182,0,45,0,0,226,0,36,0,24,24,3,3,12,12,0,22.5,22.5,145.5,145.5,1721,1721,0,70,0,8,0,3,2,2,0,39,0,0,10,11,0,8,0,36,0,0,5,6,0,0,11,0,3
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[262.8313648700714,472.7887783050537]

=== LOG SUMMARY ===
{"entries":[{"error_logs":2489,"error_pct":19.3,"service":"ts-seat-service","total_logs":12895},{"error_logs":269,"error_pct":17.03,"service":"ts-food-service","total_logs":1580},{"error_logs":95,"error_pct":25.0,"service":"ts-notification-service","total_logs":380},{"error_logs":95,"error_pct":25.0,"service":"ts-delivery-service","total_logs":380},{"error_logs":73,"error_pct":4.68,"service":"ts-preserve-service","total_logs":1561},{"error_logs":73,"error_pct":1.54,"service":"ts-order-service","total_logs":4730},{"error_logs":61,"error_pct":11.47,"service":"ts-consign-service","total_logs":532},{"error_logs":17,"error_pct":100.0,"service":"mysql","total_logs":17}],"mode":"errors","omitted_services":23,"service_count":31}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":49624.1,"error_pct":79.55,"p95_during_ms":30014.43080055,"p95_pre_ms":60.36193339999998,"service":"ts-consign-service","spans":545},{"delta_pct":-80.3,"error_pct":0.0,"p95_during_ms":14.520054199999997,"p95_pre_ms":73.6204134,"service":"ts-payment-service","spans":370},{"delta_pct":-72.1,"error_pct":0.0,"p95_during_ms":9.904089249999998,"p95_pre_ms":35.45796475,"service":"ts-assurance-service","spans":602},{"delta_pct":-65.4,"error_pct":0.0,"p95_during_ms":8.73948409999999,"p95_pre_ms":25.242079799999896,"service":"ts-train-food-service","spans":1843},{"delta_pct":-55.3,"error_pct":0.0,"p95_during_ms":525.0105379999995,"p95_pre_ms":1175.0906553000013,"service":"ts-route-plan-service","spans":1324},{"delta_pct":-53.6,"error_pct":0.0,"p95_during_ms":12.533426849999918,"p95_pre_ms":27.01305549999997,"service":"ts-price-service","spans":3370},{"delta_pct":-52.8,"error_pct":0.0,"p95_during_ms":8.664975,"p95_pre_ms":18.355991599999996,"service":"ts-config-service","spans":12460},{"delta_pct":-51.4,"error_pct":0.0,"p95_during_ms":5.695646999999999,"p95_pre_ms":11.719494199999907,"service":"ts-user-service","spans":4970}],"omitted_services":21,"service_count":29}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=35 omitted_edges=1
[{"evidence_source":"metric","onset_rel_s":255.6,"rank":1,"service":"ts-user-service","severity_z":14.957},{"evidence_source":"metric","onset_rel_s":267.6,"rank":2,"service":"rabbitmq","severity_z":20.715},{"evidence_source":"trace","onset_rel_s":272.4,"rank":3,"service":"ts-ui-dashboard","severity_z":12.736},{"evidence_source":"trace","onset_rel_s":272.4,"rank":4,"service":"loadgenerator","severity_z":12.736},{"evidence_source":"metric","onset_rel_s":322.2,"rank":5,"service":"mysql","severity_z":18.596},{"evidence_source":"metric","onset_rel_s":335.4,"rank":6,"service":"ts-assurance-service","severity_z":11.226},{"evidence_source":"trace","onset_rel_s":351.6,"rank":7,"service":"ts-station-service","severity_z":13.73},{"evidence_source":"metric","onset_rel_s":405.6,"rank":8,"service":"ts-avatar-service","severity_z":21.029},{"evidence_source":"trace","onset_rel_s":470.4,"rank":9,"service":"ts-order-service","severity_z":154.9},{"evidence_source":"none","onset_rel_s":null,"rank":10,"service":"ts-consign-service","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":11,"service":"ts-basic-service","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":12,"service":"ts-gateway-service","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":13,"service":"ts-auth-service","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":14,"service":"ts-voucher-service","severity_z":0.0}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"ts-ui-dashboard","caller":"loadgenerator"},{"callee":"ts-station-service","caller":"ts-basic-service"},{"callee":"ts-assurance-service","caller":"ts-ui-dashboard"},{"callee":"ts-auth-service","caller":"ts-ui-dashboard"},{"callee":"ts-consign-service","caller":"ts-ui-dashboard"},{"callee":"ts-order-service","caller":"ts-ui-dashboard"},{"callee":"ts-user-service","caller":"ts-ui-dashboard"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

[excluded before optimizer]

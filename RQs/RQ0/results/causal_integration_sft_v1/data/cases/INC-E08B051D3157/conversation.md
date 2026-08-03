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
opaque_id: INC-E08B051D3157
observation_window={"duration_rel_s":479.846,"source_metric_rows":1080}
selection_summary={"candidate_count":104,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":998,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["loadgenerator","loadgenerator-785d5fb59-8t5pr","mysql","mysql-0","rabbitmq","rabbitmq-0","ts-admin-basic-info-service","ts-admin-basic-info-service-b895cdd69-t5lmm","ts-admin-order-service","ts-admin-order-service-7875cc9676-4ftvb","ts-admin-route-service","ts-admin-route-service-65cc8cd669-jhs7l","ts-admin-travel-service","ts-admin-travel-service-79487c5956-kkhwq","ts-admin-user-service","ts-admin-user-service-58ffc9f45f-wk9l4","ts-assurance-service","ts-assurance-service-94c7df99f-5t99k","ts-auth-service","ts-auth-service-77d85c69dd-k4kzr","ts-avatar-service","ts-avatar-service-7c7c4d64b6-hf4cm","ts-basic-service","ts-basic-service-5bdf7474bd-dpnbg","ts-cancel-service","ts-cancel-service-66bcbdcdb8-m2g77","ts-config-service","ts-config-service-7686c57bbd-xvvv8","ts-consign-price-service","ts-consign-price-service-585746d54c-c4dd7","ts-consign-service","ts-consign-service-5b4fc59b95-nd78r","ts-contacts-service","ts-contacts-service-5f977d6595-zp5xd","ts-delivery-service","ts-delivery-service-574b957b7d-2fzp2","ts-execute-service","ts-execute-service-55c8b8c85c-lb6qd","ts-food-delivery-service","ts-food-delivery-service-6fdbfd8b5-tf84m","ts-food-service","ts-food-service-5c89cbd9b6-vd9x9","ts-gateway-service","ts-gateway-service-6b447657b4-jrrst","ts-inside-payment-service","ts-inside-payment-service-865c45d45-tmv6p","ts-news-service","ts-news-service-7869d45c45-bd5jj","ts-notification-service","ts-notification-service-59744d66d5-tnf8x","ts-order-other-service","ts-order-other-service-54467c8fd5-r56pv","ts-order-service","ts-order-service-66c6db4f9d-2kvfx","ts-payment-service","ts-payment-service-76f8cc59b8-v8dv9","ts-preserve-other-service","ts-preserve-other-service-7c564bfbf7-z2g45","ts-preserve-service","ts-preserve-service-84ccbbd47d-tpw86","ts-price-service","ts-price-service-74c479b7f9-6kwt5","ts-rebook-service","ts-rebook-service-58c78d4854-7mgcv","ts-route-plan-service","ts-route-plan-service-67d8f8fbbf-bmzl9","ts-route-service","ts-route-service-f6fbc58bc-phngt","ts-seat-service","ts-seat-service-5d77c89dc-mh6rb","ts-security-service","ts-security-service-6ccc7f574d-v6t9g","ts-station-food-service","ts-station-food-service-6946c6dbf7-dlqq2","ts-station-service","ts-station-service-6d7c454d54-rspfp","ts-ticket-office-service","ts-ticket-office-service-58645d4ff-v6wct","ts-train-food-service","ts-train-food-service-5d47bdcd87-th2jf","ts-train-service","ts-train-service-7c76856-t9hxs","ts-travel-plan-service","ts-travel-plan-service-6f7bb6dccd-wbkrk","ts-travel-service","ts-travel-service-669d7cb98b-s6q6m","ts-travel2-service","ts-travel2-service-8597bd544d-bmtfr","ts-ui-dashboard","ts-ui-dashboard-7b6fff4695-s6kj4","ts-user-service","ts-user-service-74d64f7bf7-pn886","ts-verification-code-service","ts-verification-code-service-86c65784d9-br6sr","ts-voucher-service","ts-voucher-service-58698784bc-dsk65","ts-wait-order-service","ts-wait-order-service-6cd9578878-gntk4","worker1","worker2","worker3","worker4","worker5","worker6"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[3.749,11.246,18.744,26.242,33.739,41.237,48.734,56.232,63.73,71.227,78.725,86.222,93.72,101.217,108.715,116.213,123.71,131.208,138.705,146.203,153.701,161.198,168.696,176.193,183.691,191.189,198.686,206.184,213.681,221.179,228.677,236.174,243.672,251.169,258.667,266.165,273.662,281.16,288.657,296.155,303.652,311.15,318.648,326.145,333.643,341.14,348.638,356.136,363.633,371.131,378.628,386.126,393.624,401.121,408.619,416.116,423.614,431.112,438.609,446.107,453.604,461.102,468.599,476.097]
[M1] rank=1 service=ts-ui-dashboard metric=hubble_http_request_duration_p50_seconds baseline=0.031777 peak=7.5 signed_z=363.577 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.027308,-0.004308,0.054885,-0.02601,-0.029976,-0.000241,-0.004719,-0.003286,0.001243,0.008167,7.476937,-7.485685,0.01131,7.474375,-7.491346,0.011846
missing_mask_bits=1011101110111011101110111011101110111011101110111011101110111011
observed_counts_compact=csv:0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0
[M2] rank=2 service=ts-preserve-service metric=k8s.pod.filesystem.usage baseline=805376.0 peak=19197952.0 signed_z=270.256 onset_bin=32 onset_rel_s=243.672 persistence_bins=32
values_compact=delta:718848,10240,0,4096,4096,4096,0,0,6144,2048,2048,2048,4096,8192,4096,10240,10240,16384,8192,12288,12288,14336,10240,0,12288,8192,8192,10240,2048,12288,8192,4096,129024,505856,575488,534528,503808,638976,454656,520192,714752,628736,405504,688128,606208,557056,669696,620544,632832,681984,593920,647168,673792,522240,276480,632832,677888,497664,679936,663552,487424,671744,657408,518144
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,2,1,2,1,2,1,2,1,1,2,2,1,2,1,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1
[M3] rank=3 service=ts-seat-service metric=container.memory.usage baseline=736837461.333333 peak=1397141504.0 signed_z=117.15 onset_bin=54 onset_rel_s=408.619 persistence_bins=10
values_compact=delta:734322688,0,0,-4882432,0,-12288,0,120832,120832,15056896,0,-4317184,-4317184,-1937408,-1937408,-155648,-155648,0,3600384,0,0,3694592,409600,598016,598016,233472,0,-83968,-83968,0,7516160,0,-5632000,0,0,131072,0,536576,536576,-114688,0,47104,47104,282624,0,2240512,0,544768,-479232,0,778240,0,-770048,0,21282816,0,115679232,52965376,52965376,72337408,72337408,0,149217280,56909824
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M4] rank=4 service=ts-seat-service metric=container.memory.working_set baseline=736452437.333333 peak=1396756480.0 signed_z=117.15 onset_bin=54 onset_rel_s=408.619 persistence_bins=10
values_compact=delta:733937664,0,0,-4882432,0,-12288,0,120832,120832,15056896,0,-4317184,-4317184,-1937408,-1937408,-155648,-155648,0,3600384,0,0,3694592,409600,598016,598016,233472,0,-83968,-83968,0,7516160,0,-5632000,0,0,131072,0,536576,536576,-114688,0,47104,47104,282624,0,2240512,0,544768,-479232,0,778240,0,-770048,0,21282816,0,115679232,52965376,52965376,72337408,72337408,0,149217280,56909824
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M5] rank=5 service=ts-seat-service metric=container.memory.available baseline=2484773034.666667 peak=1824468992.0 signed_z=-117.15 onset_bin=54 onset_rel_s=408.619 persistence_bins=10
values_compact=delta:2487287808,0,0,4882432,0,12288,0,-120832,-120832,-15056896,0,4317184,4317184,1937408,1937408,155648,155648,0,-3600384,0,0,-3694592,-409600,-598016,-598016,-233472,0,83968,83968,0,-7516160,0,5632000,0,0,-131072,0,-536576,-536576,114688,0,-47104,-47104,-282624,0,-2240512,0,-544768,479232,0,-778240,0,770048,0,-21282816,0,-115679232,-52965376,-52965376,-72337408,-72337408,0,-149217280,-56909824
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M6] rank=6 service=ts-seat-service metric=container.memory.rss baseline=725725525.333333 peak=1384603648.0 signed_z=117.044 onset_bin=54 onset_rel_s=408.619 persistence_bins=10
values_compact=delta:723406848,0,0,-5165056,0,221184,0,112640,112640,15040512,0,-4448256,-4448256,-1949696,-1949696,-6144,-6144,0,3346432,0,0,3944448,409600,104448,104448,970752,0,43008,43008,0,7516160,0,-5607424,0,0,143360,0,18432,18432,925696,0,34816,34816,36864,0,2457600,0,20480,32768,0,16384,0,8192,0,20983808,0,115363840,52912128,52912128,72333312,72333312,0,148910080,56655872
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M7] rank=7 service=ts-seat-service metric=k8s.pod.memory.usage baseline=735871829.333333 peak=1384951808.0 signed_z=116.254 onset_bin=54 onset_rel_s=408.619 persistence_bins=10
values_compact=delta:729997312,57344,57344,0,-12288,0,512000,-122880,-122880,0,3411968,0,-925696,0,0,-315392,372736,0,3051520,1951744,1951744,0,663552,0,192512,0,0,806912,0,573440,6979584,0,0,-5611520,0,630784,0,-241664,0,671744,106496,0,0,286720,2740224,0,-503808,18432,18432,135168,135168,0,282624,0,14209024,56236032,56236032,58116096,58116096,71014400,71014400,58183680,58183680,67946496
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M8] rank=8 service=ts-seat-service metric=k8s.pod.memory.working_set baseline=735486805.333333 peak=1384566784.0 signed_z=116.254 onset_bin=54 onset_rel_s=408.619 persistence_bins=10
values_compact=delta:729612288,57344,57344,0,-12288,0,512000,-122880,-122880,0,3411968,0,-925696,0,0,-315392,372736,0,3051520,1951744,1951744,0,663552,0,192512,0,0,806912,0,573440,6979584,0,0,-5611520,0,630784,0,-241664,0,671744,106496,0,0,286720,2740224,0,-503808,18432,18432,135168,135168,0,282624,0,14209024,56236032,56236032,58116096,58116096,71014400,71014400,58183680,58183680,67946496
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M9] rank=9 service=ts-seat-service metric=k8s.pod.memory.node.utilization baseline=0.00545 peak=0.010257 signed_z=116.254 onset_bin=54 onset_rel_s=408.619 persistence_bins=10
values_compact=delta:0.005406,0.000001,0,0,0,0,0.000004,-0.000001,-0.000001,0,0.000025,0,-0.000007,0,0,-0.000002,0.000003,0,0.000022,0.000015,0.000014,0,0.000005,0,0.000002,0,0,0.000006,0,0.000004,0.000052,0,0,-0.000042,0,0.000005,0,-0.000002,0,0.000005,0.000001,0,0,0.000002,0.00002,0,-0.000004,0,0.000001,0.000001,0.000001,0,0.000002,0,0.000105,0.000416,0.000417,0.00043,0.000431,0.000526,0.000525,0.000431,0.000431,0.000503
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M10] rank=10 service=ts-seat-service metric=k8s.pod.memory.available baseline=2485738666.666667 peak=1836658688.0 signed_z=-116.254 onset_bin=54 onset_rel_s=408.619 persistence_bins=10
values_compact=delta:2491613184,-57344,-57344,0,12288,0,-512000,122880,122880,0,-3411968,0,925696,0,0,315392,-372736,0,-3051520,-1951744,-1951744,0,-663552,0,-192512,0,0,-806912,0,-573440,-6979584,0,0,5611520,0,-630784,0,241664,0,-671744,-106496,0,0,-286720,-2740224,0,503808,-18432,-18432,-135168,-135168,0,-282624,0,-14209024,-56236032,-56236032,-58116096,-58116096,-71014400,-71014400,-58183680,-58183680,-67946496
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M11] rank=11 service=ts-seat-service metric=k8s.pod.memory_limit_utilization baseline=0.228445 peak=0.429946 signed_z=116.254 onset_bin=54 onset_rel_s=408.619 persistence_bins=10
values_compact=delta:0.226621,0.000018,0.000018,0,-0.000004,0,0.000159,-0.000038,-0.000039,0,0.00106,0,-0.000288,0,0,-0.000098,0.000116,0,0.000947,0.000606,0.000606,0,0.000206,0,0.00006,0,0,0.00025,0,0.000178,0.002167,0,0,-0.001742,0,0.000196,0,-0.000075,0,0.000209,0.000033,0,0,0.000089,0.00085,0,-0.000156,0.000006,0.000005,0.000042,0.000042,0,0.000088,0,0.004411,0.017458,0.017458,0.018042,0.018041,0.022046,0.022046,0.018062,0.018063,0.021093
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M12] rank=12 service=ts-seat-service metric=k8s.pod.memory.rss baseline=724041898.666667 peak=1372057600.0 signed_z=115.643 onset_bin=54 onset_rel_s=408.619 persistence_bins=10
values_compact=delta:718442496,-81920,-81920,0,196608,0,249856,4096,4096,0,2322432,0,-114688,0,0,-36864,53248,0,3342336,1955840,1955840,0,413696,0,208896,0,0,1069056,0,49152,7487488,0,0,-5582848,0,118784,0,16384,0,946176,69632,0,0,36864,2457600,0,12288,14336,14336,6144,6144,0,24576,0,14692352,55584768,55584768,58155008,58155008,71284736,71284736,57675776,57675776,68192256
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[299.9302227497101,474.92906880378723]

=== LOG SUMMARY ===
{"entries":[{"error_logs":5563,"error_pct":100.0,"service":"ts-ui-dashboard","total_logs":5563},{"error_logs":1159,"error_pct":10.29,"service":"ts-preserve-service","total_logs":11262},{"error_logs":1110,"error_pct":5.25,"service":"ts-basic-service","total_logs":21158},{"error_logs":252,"error_pct":16.9,"service":"ts-food-service","total_logs":1491},{"error_logs":66,"error_pct":25.0,"service":"ts-delivery-service","total_logs":264},{"error_logs":66,"error_pct":25.0,"service":"ts-notification-service","total_logs":264},{"error_logs":47,"error_pct":0.49,"service":"ts-order-service","total_logs":9664}],"mode":"errors","omitted_services":24,"service_count":31}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":1811.8,"error_pct":5.77,"p95_during_ms":5556.901060549999,"p95_pre_ms":290.661113,"service":"ts-ui-dashboard","spans":5561},{"delta_pct":-96.4,"error_pct":0.0,"p95_during_ms":41.84059785,"p95_pre_ms":1155.606168,"service":"ts-food-service","spans":1591},{"delta_pct":-63.9,"error_pct":42.85,"p95_during_ms":253.10586779999952,"p95_pre_ms":701.1775911999988,"service":"ts-preserve-service","spans":8584},{"delta_pct":-60.0,"error_pct":0.0,"p95_during_ms":10.187778349999999,"p95_pre_ms":25.48041840000008,"service":"ts-consign-service","spans":395},{"delta_pct":-57.4,"error_pct":0.0,"p95_during_ms":3.7916816,"p95_pre_ms":8.89455789999999,"service":"ts-assurance-service","spans":594},{"delta_pct":-52.3,"error_pct":0.0,"p95_during_ms":14.94898695,"p95_pre_ms":31.355650799999985,"service":"ts-seat-service","spans":18007},{"delta_pct":-45.7,"error_pct":0.0,"p95_during_ms":31.348555800000003,"p95_pre_ms":57.679324,"service":"ts-basic-service","spans":15765},{"delta_pct":-43.8,"error_pct":0.0,"p95_during_ms":77.45426700000002,"p95_pre_ms":137.86692009999982,"service":"ts-travel-service","spans":18084}],"omitted_services":22,"service_count":30}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=35 omitted_edges=0
[{"evidence_source":"metric","onset_rel_s":329.4,"rank":1,"service":"ts-travel-service","severity_z":25.464},{"evidence_source":"metric","onset_rel_s":334.8,"rank":2,"service":"ts-station-service","severity_z":10.726},{"evidence_source":"metric","onset_rel_s":339.0,"rank":3,"service":"ts-price-service","severity_z":11.63},{"evidence_source":"metric","onset_rel_s":345.0,"rank":4,"service":"ts-contacts-service","severity_z":16.326},{"evidence_source":"metric","onset_rel_s":355.8,"rank":5,"service":"ts-security-service","severity_z":44.403},{"evidence_source":"metric","onset_rel_s":360.0,"rank":6,"service":"ts-preserve-service","severity_z":270.256},{"evidence_source":"metric","onset_rel_s":367.8,"rank":7,"service":"ts-order-other-service","severity_z":22.339},{"evidence_source":"metric","onset_rel_s":384.0,"rank":8,"service":"mysql","severity_z":11.168},{"evidence_source":"metric","onset_rel_s":400.8,"rank":9,"service":"ts-avatar-service","severity_z":10.935},{"evidence_source":"metric","onset_rel_s":433.8,"rank":10,"service":"rabbitmq","severity_z":18.975},{"evidence_source":"metric","onset_rel_s":449.4,"rank":11,"service":"ts-seat-service","severity_z":117.15},{"evidence_source":"trace","onset_rel_s":454.8,"rank":12,"service":"ts-ui-dashboard","severity_z":4.365},{"evidence_source":"metric","onset_rel_s":460.8,"rank":13,"service":"ts-preserve-other-service","severity_z":17.587},{"evidence_source":"metric","onset_rel_s":469.2,"rank":14,"service":"ts-config-service","severity_z":19.544}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"ts-contacts-service","caller":"ts-preserve-service"},{"callee":"ts-seat-service","caller":"ts-preserve-service"},{"callee":"ts-security-service","caller":"ts-preserve-service"},{"callee":"ts-travel-service","caller":"ts-preserve-service"},{"callee":"ts-config-service","caller":"ts-seat-service"},{"callee":"ts-order-other-service","caller":"ts-seat-service"},{"callee":"ts-order-other-service","caller":"ts-security-service"},{"callee":"ts-seat-service","caller":"ts-travel-service"},{"callee":"ts-contacts-service","caller":"ts-ui-dashboard"},{"callee":"ts-order-other-service","caller":"ts-ui-dashboard"},{"callee":"ts-preserve-service","caller":"ts-ui-dashboard"},{"callee":"ts-travel-service","caller":"ts-ui-dashboard"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

[excluded before optimizer]

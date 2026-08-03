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
opaque_id: INC-884B31EFD601
observation_window={"duration_rel_s":478.928,"source_metric_rows":975}
selection_summary={"candidate_count":103,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":1004,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["loadgenerator","loadgenerator-8465b66847-kcvjv","mysql","mysql-0","rabbitmq","rabbitmq-0","ts-admin-basic-info-service","ts-admin-basic-info-service-c7f4d66f9-6z4pw","ts-admin-order-service","ts-admin-order-service-8578fdc446-9khmf","ts-admin-route-service","ts-admin-route-service-5d945db787-w98nx","ts-admin-travel-service","ts-admin-travel-service-96cbcb44b-pvcgl","ts-admin-user-service","ts-admin-user-service-5d8d74d79c-875q6","ts-assurance-service","ts-assurance-service-79876db68f-sxvl4","ts-auth-service","ts-auth-service-5dd97d5ccd-qgnn6","ts-avatar-service","ts-avatar-service-9b66c896d-22mzz","ts-basic-service","ts-basic-service-68f7cbd746-hbb52","ts-cancel-service","ts-cancel-service-6cb859955d-65wnj","ts-config-service","ts-config-service-7c55667486-nwvjh","ts-consign-price-service","ts-consign-price-service-6cffbf7945-l7qzk","ts-consign-service","ts-consign-service-745946dd49-v59kw","ts-contacts-service","ts-contacts-service-657d4cdfbf-dph8p","ts-delivery-service","ts-delivery-service-6b488868b8-qr2mh","ts-execute-service","ts-execute-service-86d5f5db59-sntcm","ts-food-delivery-service","ts-food-delivery-service-56447bd89f-gmn5h","ts-food-service","ts-food-service-5fd45cf66d-99vnd","ts-gateway-service","ts-gateway-service-669b9cf6bb-csnl8","ts-inside-payment-service","ts-inside-payment-service-5548965b7f-z7jqv","ts-news-service","ts-news-service-6d6c6d7855-6s5zt","ts-notification-service","ts-notification-service-5f7c7d45c9-nvwr7","ts-order-other-service","ts-order-other-service-68fb6fd887-g2wcr","ts-order-service","ts-order-service-56b9db98d8-8nljz","ts-payment-service","ts-payment-service-7648bd9bcd-kdb2n","ts-preserve-other-service","ts-preserve-other-service-5748c886c9-2f4mm","ts-preserve-service","ts-preserve-service-7684df89bd-8sbzk","ts-price-service","ts-price-service-7494fb49fc-hv5qq","ts-rebook-service","ts-rebook-service-546f7bdbbd-mjt4k","ts-route-plan-service","ts-route-plan-service-d9557d6d7-4flf9","ts-route-service","ts-route-service-86dcd6b94f-9ks6n","ts-seat-service","ts-seat-service-75676c6d97-5gcdj","ts-security-service","ts-security-service-7cddbd789d-d8h7h","ts-station-food-service","ts-station-food-service-8c666b479-p9dts","ts-station-service","ts-station-service-7ff47b8db8-chxz8","ts-ticket-office-service","ts-ticket-office-service-5c75d795c-v7hnm","ts-train-food-service","ts-train-food-service-7b67f6b66f-d5csk","ts-train-service","ts-train-service-7b65db49f4-khclm","ts-travel-plan-service","ts-travel-plan-service-5b7bdc7c56-qs54t","ts-travel-service","ts-travel-service-7f856dcb7b-6tbkw","ts-travel2-service","ts-travel2-service-79fb6f545d-6qspc","ts-ui-dashboard","ts-ui-dashboard-64f6f55bb5-8d62g","ts-user-service","ts-user-service-58c56cb98c-dds8n","ts-verification-code-service","ts-verification-code-service-57cddfb855-4zz99","ts-voucher-service","ts-voucher-service-6b7fbfc649-lp5bh","ts-wait-order-service","ts-wait-order-service-74df69f44-jqbkg","worker1","worker2","worker3","worker4","worker5"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[3.742,11.225,18.708,26.191,33.675,41.158,48.641,56.124,63.608,71.091,78.574,86.057,93.541,101.024,108.507,115.99,123.474,130.957,138.44,145.923,153.407,160.89,168.373,175.856,183.34,190.823,198.306,205.79,213.273,220.756,228.239,235.723,243.206,250.689,258.172,265.656,273.139,280.622,288.105,295.589,303.072,310.555,318.038,325.522,333.005,340.488,347.971,355.455,362.938,370.421,377.904,385.388,392.871,400.354,407.837,415.321,422.804,430.287,437.77,445.254,452.737,460.22,467.703,475.187]
[M1] rank=1 service=ts-order-service metric=container.filesystem.usage baseline=466944.0 peak=3080192.0 signed_z=848.404 onset_bin=33 onset_rel_s=250.689 persistence_bins=31
values_compact=rle:466944*33,3080192*31
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M2] rank=2 service=ts-security-service metric=hubble_http_request_duration_p50_seconds baseline=0.033423 peak=6.875 signed_z=329.565 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.031875,-0.008482,0.000808,-0.001701,0.0075,0.0575,-0.06,-0.007083,0.002708,6.799792,0.052083,0,0,0,0,0
missing_mask_bits=1011101110111011101110111011101110111011101110111011101110111011
observed_counts_compact=csv:0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0
[M3] rank=3 service=ts-security-service metric=k8s.pod.filesystem.usage baseline=553984.0 peak=5513216.0 signed_z=228.217 onset_bin=33 onset_rel_s=250.689 persistence_bins=31
values_compact=delta:512000,0,6144,2048,4096,4096,4096,4096,2048,2048,4096,4096,4096,4096,0,4096,0,0,4096,0,2048,2048,0,0,2048,2048,0,4096,0,4096,2048,6144,8192,40960,90112,57344,139264,155648,139264,208896,184320,110592,196608,196608,98304,196608,161792,133120,163840,196608,155648,172032,172032,188416,180224,180224,188416,172032,172032,188416,163840,180224,159744,172032
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1
[M4] rank=4 service=ts-order-service metric=k8s.pod.filesystem.usage baseline=1144917.333333 peak=32083968.0 signed_z=150.452 onset_bin=33 onset_rel_s=250.689 persistence_bins=31
values_compact=delta:741376,22528,30720,28672,36864,26624,34816,32768,32768,28672,36864,34816,38912,36864,20480,18432,18432,2048,6144,8192,12288,16384,8192,8192,4096,20480,20480,22528,18432,34816,38912,40960,262144,3743744,937984,1433600,2068480,2123776,2484224,2897920,2340864,2174976,2863104,1964032,-9328640,2738176,2447360,2037760,2549760,-3420160,-3608576,2670592,2662400,2379776,2785280,-9689088,2500608,2566144,2455552,2756608,-11239424,2437120,2510848,2740224
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M5] rank=5 service=ts-security-service metric=hubble_http_request_duration_p99_seconds baseline=0.129235 peak=7.4875 signed_z=49.758 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.0735,-0.020525,0.428275,-0.4514,0.04415,0.169,-0.1935,-0.019692,2.457567,4.999083,0.001042,0,0,0,0,0
missing_mask_bits=1011101110111011101110111011101110111011101110111011101110111011
observed_counts_compact=csv:0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0
[M6] rank=6 service=ts-order-service metric=hubble_http_request_duration_p95_seconds baseline=0.041852 peak=0.965 signed_z=29.729 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.039167,-0.029468,-0.000245,-0.000081,0.038544,0.033583,0.01475,-0.054792,-0.020208,0.545417,-0.016667,-0.13,0.545,-0.565,-0.085,0.070714
missing_mask_bits=0111011101110111011101110111011101110111011101110111011101110111
observed_counts_compact=csv:1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0
[M7] rank=7 service=ts-order-service metric=hubble_http_request_duration_p50_seconds baseline=0.009323 peak=0.142857 signed_z=17.6 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.005658,-0.001709,-0.000214,0.003548,0.017717,-0.006,-0.012333,-0.003372,0.096705,-0.010714,0.053571,-0.027857,-0.0325,0.015,0.0025,0.0375
missing_mask_bits=1110111011101110111011101110111011101110111011101110111011101110
observed_counts_compact=csv:0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1
[M8] rank=8 service=ts-food-service metric=hubble_http_request_duration_p90_seconds baseline=0.065098 peak=0.486375 signed_z=16.206 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.0565,-0.006857,-0.016755,0.020312,0.0393,0.025,-0.045,-0.02645,0.440325,-0.438437,-0.019313,0.005375,-0.00375,0.00375
missing_mask_bits=1011110111011101110111011101110111011111110111011111110111011101
observed_counts_compact=rle:0*1,1*1,0*4,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*7,1*1,0*3,1*1,0*7,1*1,0*3,1*1,0*3,1*1,0*1
[M9] rank=9 service=ts-order-other-service metric=hubble_http_request_duration_p95_seconds baseline=0.027522 peak=0.35 signed_z=12.954 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.022375,-0.012764,-0.000155,0.000174,0.05287,0.01375,-0.055536,-0.011074,-0.000303,-0.00017,0.00002,-0.001187,0,0.342
missing_mask_bits=0111011101110111011101110111011101111111111101110111011101110111
observed_counts_compact=rle:1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*11,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3,1*1,0*3
[M10] rank=10 service=ts-assurance-service metric=container.cpu.usage baseline=0.026066 peak=0.167555 signed_z=12.646 onset_bin=32 onset_rel_s=243.206 persistence_bins=2
values_compact=delta:0.020006,0.002476,0,0.009211,-0.003142,-0.003141,0,0.018584,0,0,0.006293,-0.009418,0,0,-0.005521,0,-0.006939,-0.006939,-0.00565,-0.005649,0,0.010596,0,0,-0.004798,0,0.004494,0,-0.002968,-0.002968,0.00168,0.001679,0.074834,0.074835,-0.161302,0,0.000111,0.00011,0.000531,0.000531,-0.000927,-0.000927,0.000918,0.000917,0,-0.00246,-0.000379,-0.000378,0.007731,0.00773,-0.014339,0,0.001224,0.001224,0,-0.002715,0,0,0.000634,0.000869,0,-0.001632,0,0.001246
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1
[M11] rank=11 service=ts-assurance-service metric=k8s.pod.cpu.node.utilization baseline=0.000204 peak=0.001301 signed_z=10.938 onset_bin=32 onset_rel_s=243.206 persistence_bins=3
values_compact=delta:0.000118,0.000094,-0.000008,-0.000009,0.00001,0.00001,0,0.000158,0,-0.000115,0.000074,0.000074,-0.000002,-0.000001,-0.000119,-0.00012,0,-0.000015,0,-0.000045,0.000004,0.000003,0.000046,0.000047,-0.000096,0,0.000032,0.000032,-0.000027,-0.000026,0.000006,0.000006,0.000585,0.000585,0,-0.001258,0.00001,0.000009,0,-0.000003,-0.000011,-0.000011,0.000013,0.000013,-0.000033,0,0.000005,0.000005,0.000061,0.000062,-0.000061,-0.000061,0.000012,0.000013,0,-0.000026,0,0.000009,0.000003,0.000003,-0.000023,0,0.000006,0.000006
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1
[M12] rank=12 service=ts-assurance-service metric=k8s.pod.cpu.usage baseline=0.026093 peak=0.166512 signed_z=10.938 onset_bin=32 onset_rel_s=243.206 persistence_bins=3
values_compact=delta:0.015054,0.012129,-0.001096,-0.001096,0.001239,0.001239,0,0.020325,0,-0.014784,0.009471,0.009471,-0.000179,-0.000179,-0.015299,-0.015299,0,-0.001886,0,-0.005777,0.000435,0.000435,0.005956,0.005955,-0.012329,0,0.00414,0.004139,-0.003447,-0.003447,0.00078,0.000779,0.074892,0.074891,0,-0.160964,0.001186,0.001187,0,-0.000355,-0.001394,-0.001395,0.001619,0.00162,-0.004152,0,0.00065,0.00065,0.007826,0.007825,-0.007812,-0.007812,0.001628,0.001628,0,-0.003268,0,0.001094,0.000368,0.000368,-0.00296,0,0.000805,0.000805
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[243.93010878562927,478.9282932281494]

=== LOG SUMMARY ===
{"entries":[{"error_logs":5352,"error_pct":100.0,"service":"ts-ui-dashboard","total_logs":5352},{"error_logs":5002,"error_pct":34.31,"service":"ts-order-service","total_logs":14577},{"error_logs":308,"error_pct":30.5,"service":"ts-security-service","total_logs":1010},{"error_logs":277,"error_pct":16.63,"service":"ts-food-service","total_logs":1666},{"error_logs":96,"error_pct":25.0,"service":"ts-notification-service","total_logs":384},{"error_logs":95,"error_pct":25.0,"service":"ts-delivery-service","total_logs":380},{"error_logs":55,"error_pct":3.47,"service":"ts-preserve-service","total_logs":1586}],"mode":"errors","omitted_services":24,"service_count":31}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":7543.8,"error_pct":58.44,"p95_during_ms":60010.3362426,"p95_pre_ms":785.0817948499996,"service":"ts-preserve-service","spans":1039},{"delta_pct":7527.6,"error_pct":73.97,"p95_during_ms":4089.062736,"p95_pre_ms":53.6084865,"service":"ts-security-service","spans":2217},{"delta_pct":-79.9,"error_pct":0.0,"p95_during_ms":8.43049255,"p95_pre_ms":41.8871202,"service":"ts-consign-service","spans":713},{"delta_pct":-58.7,"error_pct":0.0,"p95_during_ms":5.9043256999999985,"p95_pre_ms":14.2810534,"service":"ts-contacts-service","spans":2262},{"delta_pct":-58.4,"error_pct":0.0,"p95_during_ms":4.5785409999999995,"p95_pre_ms":11.0080017,"service":"ts-assurance-service","spans":838},{"delta_pct":-56.3,"error_pct":0.0,"p95_during_ms":17.606044299999997,"p95_pre_ms":40.32593299999996,"service":"ts-seat-service","spans":10331},{"delta_pct":-55.4,"error_pct":60.77,"p95_during_ms":3.4657087,"p95_pre_ms":7.76972675,"service":"ts-order-service","spans":27470},{"delta_pct":-55.0,"error_pct":0.0,"p95_during_ms":8.516673699999998,"p95_pre_ms":18.91717109999998,"service":"ts-station-food-service","spans":1267}],"omitted_services":22,"service_count":30}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=35 omitted_edges=2
[{"evidence_source":"trace","onset_rel_s":244.2,"rank":1,"service":"ts-security-service","severity_z":16.589},{"evidence_source":"trace","onset_rel_s":244.2,"rank":2,"service":"ts-preserve-service","severity_z":46.764},{"evidence_source":"metric","onset_rel_s":246.0,"rank":3,"service":"ts-assurance-service","severity_z":12.646},{"evidence_source":"metric","onset_rel_s":249.0,"rank":4,"service":"ts-order-service","severity_z":848.404},{"evidence_source":"metric","onset_rel_s":255.0,"rank":5,"service":"ts-food-service","severity_z":16.206},{"evidence_source":"trace","onset_rel_s":264.6,"rank":6,"service":"ts-ui-dashboard","severity_z":34.907},{"evidence_source":"trace","onset_rel_s":264.6,"rank":7,"service":"loadgenerator","severity_z":34.686},{"evidence_source":"trace","onset_rel_s":454.2,"rank":8,"service":"ts-order-other-service","severity_z":18.7},{"evidence_source":"none","onset_rel_s":null,"rank":9,"service":"ts-avatar-service","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":10,"service":"ts-inside-payment-service","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":11,"service":"ts-admin-route-service","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":12,"service":"ts-route-plan-service","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":13,"service":"mysql","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":14,"service":"ts-payment-service","severity_z":0.0}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"ts-ui-dashboard","caller":"loadgenerator"},{"callee":"ts-order-service","caller":"ts-inside-payment-service"},{"callee":"ts-payment-service","caller":"ts-inside-payment-service"},{"callee":"ts-assurance-service","caller":"ts-preserve-service"},{"callee":"ts-food-service","caller":"ts-preserve-service"},{"callee":"ts-order-service","caller":"ts-preserve-service"},{"callee":"ts-security-service","caller":"ts-preserve-service"},{"callee":"ts-order-other-service","caller":"ts-security-service"},{"callee":"ts-order-service","caller":"ts-security-service"},{"callee":"ts-assurance-service","caller":"ts-ui-dashboard"},{"callee":"ts-food-service","caller":"ts-ui-dashboard"},{"callee":"ts-inside-payment-service","caller":"ts-ui-dashboard"},{"callee":"ts-order-other-service","caller":"ts-ui-dashboard"},{"callee":"ts-order-service","caller":"ts-ui-dashboard"},{"callee":"ts-preserve-service","caller":"ts-ui-dashboard"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

{"confidence":"high","reason":"Rank ts-order-service first because ts-order-service has direct container.filesystem.usage evidence (signed-z 848.4, persistence 31 bins); although ts-security-service is salient, the caller path ts-security-service -> ts-order-service means a disturbance in the callee can propagate back toward that caller-side symptom.","services":["ts-order-service","ts-security-service"]}

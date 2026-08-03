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
opaque_id: INC-13688565DC2D
observation_window={"duration_rel_s":480.791,"source_metric_rows":954}
selection_summary={"candidate_count":104,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":913,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["loadgenerator","loadgenerator-795bf9f84f-ht2q5","mysql","mysql-0","rabbitmq","rabbitmq-0","ts-admin-basic-info-service","ts-admin-basic-info-service-85796f6b-v6zm6","ts-admin-order-service","ts-admin-order-service-7bfb6f8859-8pkr2","ts-admin-route-service","ts-admin-route-service-76d9f59d-d588b","ts-admin-travel-service","ts-admin-travel-service-5bf9c4995-hqtv4","ts-admin-user-service","ts-admin-user-service-847fc56756-8jxq6","ts-assurance-service","ts-assurance-service-678977c776-6f965","ts-auth-service","ts-auth-service-55d864446c-62xt4","ts-avatar-service","ts-avatar-service-6c7dd65985-jfr6x","ts-basic-service","ts-basic-service-7745bb5fb7-66j9v","ts-cancel-service","ts-cancel-service-766cd985ff-vmmrl","ts-config-service","ts-config-service-f94864959-fgbj8","ts-consign-price-service","ts-consign-price-service-7d686bf77b-qxb4t","ts-consign-service","ts-consign-service-5c5b5fbd4-brqpm","ts-contacts-service","ts-contacts-service-67749d8c4d-qskx9","ts-delivery-service","ts-delivery-service-6cd84fc465-hl6ks","ts-execute-service","ts-execute-service-84f8ff5b74-gfts8","ts-food-delivery-service","ts-food-delivery-service-54946d9774-96fq5","ts-food-service","ts-food-service-579cbbf5b5-9ntmw","ts-gateway-service","ts-gateway-service-5f58fc7c9-t4hrj","ts-inside-payment-service","ts-inside-payment-service-844b7bf9fd-62xdx","ts-news-service","ts-news-service-b7d748896-5tsxn","ts-notification-service","ts-notification-service-78967d4986-bwtg9","ts-order-other-service","ts-order-other-service-6977676fc4-xkxbf","ts-order-service","ts-order-service-754957c888-wlvjj","ts-payment-service","ts-payment-service-d47c475f9-7j9hf","ts-preserve-other-service","ts-preserve-other-service-6dd5b78d46-bg9fs","ts-preserve-service","ts-preserve-service-c854c79c-nh9g5","ts-price-service","ts-price-service-57597867f6-rmbht","ts-rebook-service","ts-rebook-service-7cdbb7cddf-7fhgn","ts-route-plan-service","ts-route-plan-service-687fddf4b-w8x9n","ts-route-service","ts-route-service-78bfb68cb4-kctp6","ts-seat-service","ts-seat-service-bc9677b4d-lwqf6","ts-security-service","ts-security-service-79fc8cdf4c-7x2z8","ts-station-food-service","ts-station-food-service-67946cfd46-w2s5r","ts-station-service","ts-station-service-56b4bc59d9-wbctn","ts-ticket-office-service","ts-ticket-office-service-6cf79594d8-fxf2g","ts-train-food-service","ts-train-food-service-7d6894677b-fmtdw","ts-train-service","ts-train-service-7596dd5895-4qgcb","ts-travel-plan-service","ts-travel-plan-service-79bc466f6f-m89st","ts-travel-service","ts-travel-service-b7d886d85-bp9n9","ts-travel2-service","ts-travel2-service-586dbbf7c9-gn8rw","ts-ui-dashboard","ts-ui-dashboard-75f8554d4d-c228q","ts-user-service","ts-user-service-75fb6745f8-kqtdq","ts-verification-code-service","ts-verification-code-service-594d468ccd-vp92f","ts-voucher-service","ts-voucher-service-796cbccf68-28f5p","ts-wait-order-service","ts-wait-order-service-55b9644c6f-trzk8","worker1","worker2","worker3","worker4","worker5","worker6"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[3.756,11.269,18.781,26.293,33.806,41.318,48.83,56.343,63.855,71.367,78.88,86.392,93.904,101.417,108.929,116.442,123.954,131.466,138.979,146.491,154.003,161.516,169.028,176.54,184.053,191.565,199.078,206.59,214.102,221.615,229.127,236.639,244.152,251.664,259.176,266.689,274.201,281.713,289.226,296.738,304.251,311.763,319.275,326.788,334.3,341.812,349.325,356.837,364.349,371.862,379.374,386.887,394.399,401.911,409.424,416.936,424.448,431.961,439.473,446.985,454.498,462.01,469.522,477.035]
[M1] rank=1 service=ts-admin-route-service metric=container.cpu.usage baseline=0.005117 peak=1.011573 signed_z=999.0 onset_bin=40 onset_rel_s=304.251 persistence_bins=14
values_compact=delta:0.004846,0.000345,0,-0.00051,0,-0.000768,0.000072,0.000073,0.000756,0.000755,0,-0.000788,0,-0.00054,0.000031,0.000031,0,0.001289,0,0,-0.000334,-0.000024,0.000042,0.000041,0,0.001173,0,-0.000721,0,0.00001,0,-0.000506,0.000289,0.000289,-0.000534,-0.000534,0.000477,0.000478,0.000194,0.000195,0.502723,0.502723,0,-1.003843,0,0.000004,0.000859,0.000856,0,-0.001849,0,-0.002668,0.000399,0.000399,0.000931,0.000931,-0.000437,0,-0.001681,0,-0.00008,0,0.000143
missing_mask_bits=0000000000000000000000000000000000000000000000100000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,0,2,2,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M2] rank=2 service=ts-admin-route-service metric=k8s.pod.cpu.node.utilization baseline=4e-05 peak=0.008372 signed_z=999.0 onset_bin=41 onset_rel_s=311.763 persistence_bins=10
values_compact=rle:0.000035*2,0.00004*2,0.000037*2,0.00003*2,0.000042*2,0.00004*1,0.000038*1,0.000035*1,0.000033*2,0.000034*2,0.000043*4,0.000041*4,0.000053*3,0.000045*6,0.000042*1,0.000038*1,0.000041*1,0.000045*2,0.000048*2,0.008372*2,0.000062*2,0.000061*1,null*1,0.000068*1,0.000075*1,0.000064*1,0.000054*1,0.00006*2,0.000042*2,0.000049*1,0.000055*1,0.000054*3,0.000045*1,0.000043*1,0.00004*2
missing_mask_bits=0000000000000000000000000000000000000000000000100000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,0,2,2,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M3] rank=3 service=ts-admin-route-service metric=k8s.pod.cpu.usage baseline=0.005129 peak=1.071649 signed_z=999.0 onset_bin=41 onset_rel_s=311.763 persistence_bins=10
values_compact=delta:0.004465,0,0.000659,0,-0.000448,0,-0.000794,0,0.001556,0,-0.000315,-0.000315,-0.000274,-0.000275,0,0.000088,0,0.001126,0,0.000026,0,-0.000298,0,0.00005,0,0.001477,0,0,-0.001027,0,0.000038,0,0.000033,0,-0.000448,-0.000448,0.00043,0.00043,0,0.000405,0,1.065508,0,-1.063769,0,-0.000088,0.000857,0.000944,-0.001337,-0.001338,0.000781,0,-0.002266,0,0.000797,0.000796,-0.000065,-0.000066,0,-0.001114,-0.000311,-0.000312,-0.000085
missing_mask_bits=0000000000000000000000000000000000000000000000100000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,0,2,2,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M4] rank=4 service=ts-admin-route-service metric=k8s.pod.cpu_limit_utilization baseline=0.001026 peak=0.21433 signed_z=999.0 onset_bin=41 onset_rel_s=311.763 persistence_bins=10
values_compact=delta:0.000893,0,0.000132,0,-0.00009,0,-0.000159,0,0.000312,0,-0.000063,-0.000063,-0.000055,-0.000055,0,0.000017,0,0.000226,0,0.000005,0,-0.00006,0,0.00001,0,0.000296,0,0,-0.000206,0,0.000008,0,0.000006,0,-0.000089,-0.00009,0.000086,0.000086,0,0.000081,0,0.213102,0,-0.212754,0,-0.000018,0.000172,0.000189,-0.000268,-0.000267,0.000156,0,-0.000453,0,0.000159,0.000159,-0.000013,-0.000013,0,-0.000223,-0.000062,-0.000062,-0.000017
missing_mask_bits=0000000000000000000000000000000000000000000000100000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,0,2,2,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M5] rank=5 service=ts-cancel-service metric=container.cpu.usage baseline=0.005699 peak=0.819177 signed_z=303.767 onset_bin=61 onset_rel_s=462.01 persistence_bins=3
values_compact=rle:0.011246*1,0.008644*1,0.006043*1,0.004262*2,0.003865*2,0.003915*1,0.004097*1,0.004572*1,0.005047*2,0.011094*1,0.007486*1,0.003878*2,0.003911*3,0.005333*1,0.004874*2,0.012712*2,0.006645*3,0.004798*2,0.004487*1,0.003886*3,0.00471*2,0.005261*2,0.005004*2,0.005358*2,0.007269*2,0.006507*2,0.00593*2,0.004817*1,0.007552*1,0.006797*1,0.006042*2,0.006143*2,0.00454*2,0.008185*3,0.005888*2,0.580505*2,0.819177*1
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,2,1,2,1,2,1,2,1,2,1,1,2,2,1,2,1,2
[M6] rank=6 service=ts-cancel-service metric=k8s.pod.cpu.node.utilization baseline=5e-05 peak=0.009828 signed_z=299.04 onset_bin=62 onset_rel_s=469.522 persistence_bins=2
values_compact=delta:0.000145,0,-0.000102,0,-0.000012,0,-0.000001,0,0.000002,0,0.000005,0,0.000066,-0.000037,-0.000036,0,0.000001,0.000004,0.000004,-0.000001,0,0.000035,0.000034,-0.000032,-0.000032,0.000003,0.000004,-0.000007,-0.000007,-0.000001,-0.000001,-0.000002,-0.000002,0.000011,0,0,0,-0.000002,0,0.000002,0,0.000014,0,-0.000002,-0.000002,-0.000007,0,-0.000003,-0.000004,0.000009,0.000009,0,-0.000003,-0.000009,-0.000009,0.000003,0.000002,0,0.000032,-0.000012,-0.000013,0,0.009782,0
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,2,1,2,1,2,1,2,1,2,1,1,2,2,1,2,1,2
[M7] rank=7 service=ts-cancel-service metric=k8s.pod.cpu.usage baseline=0.006423 peak=1.25802 signed_z=299.04 onset_bin=62 onset_rel_s=469.522 persistence_bins=2
values_compact=delta:0.018537,0,-0.013057,0,-0.001531,0,-0.000149,0,0.000312,0,0.000592,0,0.00844,-0.00466,-0.00466,0.000066,0.000067,0.00049,0.00049,-0.000017,-0.000017,0.004405,0.004405,-0.004102,-0.004101,0.00042,0.00042,-0.000856,-0.000856,-0.000156,-0.000157,-0.000268,-0.000268,0.001448,0,-0.000008,-0.000008,-0.000243,0,0.000312,0,0.001712,0,-0.000216,-0.000217,-0.000906,0,-0.000452,-0.000452,0.00111,0.001111,0,-0.000296,-0.001139,-0.00114,0.000278,0.000278,0,0.004148,-0.001601,-0.001602,0,1.252114,0
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,2,1,2,1,2,1,2,1,2,1,1,2,2,1,2,1,2
[M8] rank=8 service=ts-cancel-service metric=k8s.pod.cpu_limit_utilization baseline=0.001285 peak=0.251604 signed_z=299.04 onset_bin=62 onset_rel_s=469.522 persistence_bins=2
values_compact=delta:0.003707,0,-0.002611,0,-0.000306,0,-0.00003,0,0.000062,0,0.000119,0,0.001688,-0.000932,-0.000932,0.000013,0.000013,0.000098,0.000098,-0.000003,-0.000003,0.000881,0.000881,-0.000821,-0.00082,0.000084,0.000084,-0.000171,-0.000171,-0.000032,-0.000031,-0.000054,-0.000053,0.000289,0,-0.000001,-0.000002,-0.000048,0,0.000062,0,0.000342,0,-0.000043,-0.000043,-0.000181,0,-0.000091,-0.00009,0.000222,0.000222,0,-0.000059,-0.000228,-0.000228,0.000056,0.000055,0,0.00083,-0.00032,-0.000321,0,0.250423,0
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,2,1,2,1,2,1,2,1,2,1,1,2,2,1,2,1,2
[M9] rank=9 service=ts-voucher-service metric=container.cpu.usage baseline=0.000451 peak=0.002084 signed_z=51.361 onset_bin=40 onset_rel_s=304.251 persistence_bins=15
values_compact=delta:0.000453,0.000024,-0.000018,-0.000019,0.000001,0,-0.000028,0,0.000077,0,-0.000099,0,0.000036,0,-0.000006,0,0.00002,0.00002,0.000007,0.000008,0.000005,0.000004,-0.000005,-0.000006,0.000013,0.000012,0,-0.000049,-0.000001,-0.000001,-0.00002,-0.000019,0.000032,0.000033,-0.000035,0,0.000018,0.000017,0.000012,0.000011,0.000064,0.000065,-0.000004,0,0,0.000541,0,0.000921,0,-0.000799,-0.000799,0.000231,0,-0.000197,0,-0.000027,0,0.000027,0,0.000025,0.000026,0.000336,0,-0.00043
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M10] rank=10 service=ts-station-service metric=container.cpu.usage baseline=0.044463 peak=1.762175 signed_z=50.916 onset_bin=60 onset_rel_s=454.498 persistence_bins=2
values_compact=delta:0.03713,0,0,0.006109,0,0.041702,0,-0.053967,0,0.016832,0,-0.009789,-0.009789,0.002135,0,0.113654,0,-0.051362,-0.051363,0,-0.010097,-0.003996,-0.003997,-0.003458,0,-0.001162,-0.001161,0.007738,0,0.006771,-0.009838,0,0.006328,-0.002162,-0.002161,-0.005805,-0.005804,-0.000853,-0.000852,-0.001037,-0.001036,0.00398,0.00398,0,-0.00639,0,0.001152,-0.002035,-0.003188,0,0.005882,0,0.001937,-0.002869,-0.002868,0.001575,0.001574,0,0.010174,-0.013437,1.753998,0,-1.752031,0.002435
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,2,1,2,1,2,1,2,1,2,1,1,2,2,1,2,1,2
[M11] rank=11 service=ts-voucher-service metric=k8s.pod.cpu.node.utilization baseline=4e-06 peak=1.5e-05 signed_z=46.865 onset_bin=42 onset_rel_s=319.275 persistence_bins=13
values_compact=rle:0.000004*4,0.000003*4,0.000004*4,0.000003*6,0.000004*12,0.000003*3,0.000004*9,0.000005*3,0.00001*2,0.000015*2,0.000009*1,0.000004*1,0.000005*1,0.000006*1,0.000004*7,0.000007*3,0.000003*1
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M12] rank=12 service=ts-voucher-service metric=k8s.pod.cpu.usage baseline=0.000454 peak=0.001893 signed_z=46.865 onset_bin=42 onset_rel_s=319.275 persistence_bins=15
values_compact=delta:0.000467,-0.000008,0,0,-0.000035,0,-0.000006,0,0.000038,0.000039,-0.000046,0,-0.000024,-0.000007,-0.000002,-0.000002,0,0.000025,0.000034,0.000035,-0.000019,-0.000018,0.000016,0.000016,-0.000009,-0.000009,-0.000016,0,-0.000001,-0.000001,-0.000041,0,-0.000045,0.000115,0,0,-0.000032,0,0.000024,0.000024,0.000016,0,0.000061,0.000061,0,0.000573,0,0.00067,0,-0.000708,-0.000707,0.000134,0.000133,-0.000195,0,-0.000036,-0.000036,0,0.000028,0,0.000422,0,0,-0.000487
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[302.5950367450714,329.40891003608704]

=== LOG SUMMARY ===
{"entries":[{"error_logs":1466,"error_pct":19.21,"service":"ts-seat-service","total_logs":7630},{"error_logs":170,"error_pct":16.46,"service":"ts-food-service","total_logs":1033},{"error_logs":96,"error_pct":25.0,"service":"ts-notification-service","total_logs":384},{"error_logs":96,"error_pct":25.0,"service":"ts-delivery-service","total_logs":384},{"error_logs":29,"error_pct":0.97,"service":"ts-order-service","total_logs":2985},{"error_logs":29,"error_pct":2.48,"service":"ts-preserve-service","total_logs":1169},{"error_logs":5,"error_pct":0.15,"service":"ts-ui-dashboard","total_logs":3343},{"error_logs":2,"error_pct":0.41,"service":"ts-route-plan-service","total_logs":482}],"mode":"errors","omitted_services":23,"service_count":31}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":1519.4,"error_pct":0.0,"p95_during_ms":10904.3415483,"p95_pre_ms":673.3672320499998,"service":"ts-travel-plan-service","spans":989},{"delta_pct":1164.0,"error_pct":0.0,"p95_during_ms":3883.1754306999997,"p95_pre_ms":307.20664039999986,"service":"ts-travel2-service","spans":2188},{"delta_pct":1045.3,"error_pct":0.0,"p95_during_ms":71.6040024,"p95_pre_ms":6.2519950999999825,"service":"ts-route-service","spans":15599},{"delta_pct":802.2,"error_pct":0.0,"p95_during_ms":2385.6694639999923,"p95_pre_ms":264.43802069999987,"service":"ts-ui-dashboard","spans":3342},{"delta_pct":787.1,"error_pct":0.0,"p95_during_ms":2386.346085149992,"p95_pre_ms":268.9966004499996,"service":"loadgenerator","spans":3342},{"delta_pct":763.8,"error_pct":0.0,"p95_during_ms":90.80336210000002,"p95_pre_ms":10.512579399999991,"service":"ts-train-service","spans":4569},{"delta_pct":690.6,"error_pct":0.0,"p95_during_ms":9569.980514399998,"p95_pre_ms":1210.5246104999983,"service":"ts-route-plan-service","spans":714},{"delta_pct":644.4,"error_pct":0.0,"p95_during_ms":51.366856399999996,"p95_pre_ms":6.900728399999995,"service":"ts-user-service","spans":2850}],"omitted_services":22,"service_count":30}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=35 omitted_edges=5
[{"evidence_source":"trace","onset_rel_s":305.4,"rank":1,"service":"ts-order-service","severity_z":999.0},{"evidence_source":"trace","onset_rel_s":305.4,"rank":2,"service":"ts-config-service","severity_z":646.669},{"evidence_source":"trace","onset_rel_s":305.4,"rank":3,"service":"ts-auth-service","severity_z":574.894},{"evidence_source":"trace","onset_rel_s":305.4,"rank":4,"service":"ts-station-service","severity_z":558.486},{"evidence_source":"trace","onset_rel_s":305.4,"rank":5,"service":"ts-seat-service","severity_z":293.126},{"evidence_source":"trace","onset_rel_s":305.4,"rank":6,"service":"ts-contacts-service","severity_z":258.377},{"evidence_source":"trace","onset_rel_s":305.4,"rank":7,"service":"ts-travel-service","severity_z":233.543},{"evidence_source":"trace","onset_rel_s":305.4,"rank":8,"service":"ts-route-service","severity_z":96.712},{"evidence_source":"trace","onset_rel_s":305.4,"rank":9,"service":"ts-order-other-service","severity_z":73.35},{"evidence_source":"metric","onset_rel_s":307.8,"rank":10,"service":"ts-admin-route-service","severity_z":999.0},{"evidence_source":"trace","onset_rel_s":335.4,"rank":11,"service":"ts-basic-service","severity_z":100.957},{"evidence_source":"metric","onset_rel_s":354.6,"rank":12,"service":"ts-voucher-service","severity_z":51.361},{"evidence_source":"trace","onset_rel_s":375.6,"rank":13,"service":"ts-assurance-service","severity_z":155.369},{"evidence_source":"trace","onset_rel_s":456.0,"rank":14,"service":"ts-cancel-service","severity_z":999.0}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"ts-route-service","caller":"ts-basic-service"},{"callee":"ts-station-service","caller":"ts-basic-service"},{"callee":"ts-order-service","caller":"ts-cancel-service"},{"callee":"ts-config-service","caller":"ts-seat-service"},{"callee":"ts-order-other-service","caller":"ts-seat-service"},{"callee":"ts-order-service","caller":"ts-seat-service"},{"callee":"ts-basic-service","caller":"ts-travel-service"},{"callee":"ts-route-service","caller":"ts-travel-service"},{"callee":"ts-seat-service","caller":"ts-travel-service"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

[excluded before optimizer]

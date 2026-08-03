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
opaque_id: INC-7B7596EF0C7A
observation_window={"duration_rel_s":478.576,"source_metric_rows":855}
selection_summary={"candidate_count":103,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":900,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["loadgenerator","loadgenerator-795bf9f84f-49c4l","mysql","mysql-0","rabbitmq","rabbitmq-0","ts-admin-basic-info-service","ts-admin-basic-info-service-54b7c64f8c-6dl4s","ts-admin-order-service","ts-admin-order-service-56fbfcb97d-4rqpc","ts-admin-route-service","ts-admin-route-service-6cf589c99-vb4lq","ts-admin-travel-service","ts-admin-travel-service-7c794876d6-rhlv6","ts-admin-user-service","ts-admin-user-service-5579f4b45c-kwrt8","ts-assurance-service","ts-assurance-service-76fcc7777-wsfdw","ts-auth-service","ts-auth-service-77f748d59d-74r95","ts-avatar-service","ts-avatar-service-6b6bc6f5fb-8cf2v","ts-basic-service","ts-basic-service-58895fcfbb-2hbhj","ts-cancel-service","ts-cancel-service-68fd79fb78-gwmpk","ts-config-service","ts-config-service-f889649fd-8fffk","ts-consign-price-service","ts-consign-price-service-6d8fb9cbb9-g445m","ts-consign-service","ts-consign-service-9df54f7c-npdls","ts-contacts-service","ts-contacts-service-78b7d5b545-mt5jf","ts-delivery-service","ts-delivery-service-7fbb4569b8-b94wp","ts-execute-service","ts-execute-service-7bf7fc96bc-2x8vs","ts-food-delivery-service","ts-food-delivery-service-74db8c6b7f-894t9","ts-food-service","ts-food-service-7f5b94897b-hrclk","ts-gateway-service","ts-gateway-service-6696979f58-5v2zw","ts-inside-payment-service","ts-inside-payment-service-5d79b67695-wxbt8","ts-news-service","ts-news-service-7869d45c45-llr2w","ts-notification-service","ts-notification-service-75bd8db98c-h2lzr","ts-order-other-service","ts-order-other-service-b7b9c4467-zhb8d","ts-order-service","ts-order-service-754957c888-lb5zb","ts-payment-service","ts-payment-service-684969464b-q9bjj","ts-preserve-other-service","ts-preserve-other-service-6dcc8f84c-4gddh","ts-preserve-service","ts-preserve-service-748b7d8b6d-sdshk","ts-price-service","ts-price-service-6c4b9477f7-dwpv5","ts-rebook-service","ts-rebook-service-9fcf44b4d-vmml2","ts-route-plan-service","ts-route-plan-service-dc8959c5f-nxjjv","ts-route-service","ts-route-service-9b9d5d8b9-rzk5r","ts-seat-service","ts-seat-service-7556bb78c7-5g225","ts-security-service","ts-security-service-5895b7b4f8-66k7j","ts-station-food-service","ts-station-food-service-6cc5c9556c-7s5s4","ts-station-service","ts-station-service-bc8cdcf7b-twt6c","ts-ticket-office-service","ts-ticket-office-service-776c7fc497-vshmj","ts-train-food-service","ts-train-food-service-59b97b769c-986ss","ts-train-service","ts-train-service-764f88cfd6-86j9d","ts-travel-plan-service","ts-travel-plan-service-599867b876-xvq9b","ts-travel-service","ts-travel-service-586b456996-tjh7c","ts-travel2-service","ts-travel2-service-5565b8b5d-stfmz","ts-ui-dashboard","ts-ui-dashboard-5c4477bcbf-9dvl5","ts-user-service","ts-user-service-57669bc6b7-mq224","ts-verification-code-service","ts-verification-code-service-7f4b76f56c-r4rcd","ts-voucher-service","ts-voucher-service-7c66bbc6bf-mhr4v","ts-wait-order-service","ts-wait-order-service-5f96cc4884-q6ghh","worker2","worker3","worker4","worker5","worker6"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[3.739,11.217,18.694,26.172,33.65,41.128,48.605,56.083,63.561,71.039,78.516,85.994,93.472,100.95,108.427,115.905,123.383,130.861,138.338,145.816,153.294,160.772,168.249,175.727,183.205,190.683,198.16,205.638,213.116,220.594,228.071,235.549,243.027,250.505,257.982,265.46,272.938,280.416,287.893,295.371,302.849,310.327,317.804,325.282,332.76,340.238,347.715,355.193,362.671,370.149,377.626,385.104,392.582,400.06,407.537,415.015,422.493,429.971,437.448,444.926,452.404,459.882,467.359,474.837]
[M1] rank=1 service=loadgenerator metric=container.memory.page_faults baseline=2609.104167 peak=7580.0 signed_z=156.432 onset_bin=32 onset_rel_s=243.027 persistence_bins=32
values_compact=delta:2567.5,3.5,0,3,0,2,0,0,19,2,0,3,0.5,0.5,0,0,0,4,1,1,2,0,2,2,18.5,18.5,3,3,10,0,6,0,37,10,0,1,0,0,0,0,0,281,278.5,278.5,0,696,96,96,23,0,43,0,176.5,176.5,672,672,438.5,438.5,433,0,18,18,12.5,12.5
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1
[M2] rank=2 service=loadgenerator metric=k8s.pod.memory.page_faults baseline=152867.979167 peak=157826.0 signed_z=152.46 onset_bin=33 onset_rel_s=250.505 persistence_bins=31
values_compact=delta:152827,4,0,2,0,2,4.5,4.5,0,12,0,3,0,1,0,0,1,0,5,0,2,0,4,0,11.5,11.5,0,27,2.5,2.5,13.5,13.5,10,10,4,0,1,0,0,1,0,0,439,0,702,0,571,30,0,0,41,0,156.5,156.5,649,649,524.5,524.5,0,366,0,37,0,0
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1
[M3] rank=3 service=ts-food-service metric=k8s.pod.filesystem.usage baseline=636160.0 peak=1658880.0 signed_z=31.978 onset_bin=35 onset_rel_s=265.46 persistence_bins=29
values_compact=delta:583680,6144,4096,8192,2048,2048,2048,6144,0,4096,0,0,0,4096,0,4096,4096,0,6144,6144,2048,6144,6144,6144,2048,6144,6144,2048,6144,2048,4096,4096,2048,2048,28672,8192,12288,8192,24576,24576,26624,43008,8192,12288,24576,24576,36864,53248,36864,53248,55296,83968,61440,45056,28672,12288,32768,36864,36864,32768,18432,34816,28672,24576
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1
[M4] rank=4 service=ts-station-service metric=k8s.pod.cpu.node.utilization baseline=0.000311 peak=0.006301 signed_z=31.589 onset_bin=62 onset_rel_s=467.359 persistence_bins=2
values_compact=delta:0.000192,0.000126,0.000049,0.000048,0.000105,0.000104,0,-0.000416,0,0.000076,-0.000081,-0.000081,0.000003,0.000004,-0.000001,-0.000001,0.000294,0,-0.000243,0,0.000082,-0.000038,0,0.000124,0,0,0.000595,-0.000703,0,0.000051,0,-0.000156,0.000027,0.000028,0,-0.000076,0.000008,0.000007,0.000001,0.000001,0.000011,0.000011,0.000022,0.000021,0.000008,0.000007,-0.000038,-0.000038,-0.000002,-0.000003,0,0.000005,0,0,-0.000002,0,0.000017,0.000018,0.00036,0,-0.000226,0,0.006001,0
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1
[M5] rank=5 service=ts-station-service metric=k8s.pod.cpu.usage baseline=0.039795 peak=0.806476 signed_z=31.589 onset_bin=62 onset_rel_s=467.359 persistence_bins=2
values_compact=delta:0.024564,0.016184,0.006216,0.006217,0.013334,0.013334,0,-0.05327,0,0.009777,-0.01039,-0.010391,0.000487,0.000487,-0.000163,-0.000164,0.037631,0,-0.031071,0,0.010552,-0.004862,0,0.015804,0,0,0.076135,-0.089983,0,0.006623,0,-0.020086,0.003545,0.003546,0,-0.009735,0.000977,0.000978,0.000098,0.000098,0.001459,0.001459,0.002702,0.002703,0.000997,0.000997,-0.004861,-0.004862,-0.000335,-0.000336,0,0.000583,0,0,-0.000182,0,0.002204,0.002204,0.046154,0,-0.02891,0,0.768028,0
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1
[M6] rank=6 service=ts-station-service metric=k8s.pod.cpu_limit_utilization baseline=0.007959 peak=0.161295 signed_z=31.589 onset_bin=62 onset_rel_s=467.359 persistence_bins=2
values_compact=delta:0.004913,0.003237,0.001243,0.001243,0.002667,0.002667,0,-0.010654,0,0.001955,-0.002078,-0.002078,0.000097,0.000098,-0.000033,-0.000033,0.007527,0,-0.006215,0,0.002111,-0.000973,0,0.003161,0,0,0.015227,-0.017996,0,0.001324,0,-0.004017,0.000709,0.000709,0,-0.001947,0.000196,0.000195,0.00002,0.000019,0.000292,0.000292,0.00054,0.000541,0.000199,0.0002,-0.000972,-0.000973,-0.000067,-0.000067,0,0.000117,0,0,-0.000037,0,0.000441,0.000441,0.009231,0,-0.005782,0,0.153605,0
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1
[M7] rank=7 service=ts-price-service metric=container.cpu.usage baseline=0.031914 peak=0.712124 signed_z=27.944 onset_bin=43 onset_rel_s=325.282 persistence_bins=2
values_compact=delta:0.085936,0.052028,-0.104872,0,0.008241,0,-0.009611,-0.009612,0.014747,0.014748,-0.014608,-0.014608,0,0.000874,-0.00626,-0.006259,0.023242,0,-0.006531,-0.00653,-0.00083,-0.000831,0,0.005455,0,0.011023,0,-0.019756,0,0.003458,0,-0.00419,0,0.009883,0,-0.005069,-0.004913,-0.004912,0.032055,0.032056,-0.063842,0,0.003162,0.69845,-0.349458,-0.349458,0.012219,0.012219,-0.008297,-0.008296,0.006449,0,-0.003781,-0.00378,0,0.005764,0,-0.004333,0,-0.005763,0.005438,0.005439,-0.006589,-0.006589
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1
[M8] rank=8 service=ts-assurance-service metric=container.filesystem.available baseline=14288188074.666666 peak=14810349568.0 signed_z=26.602 onset_bin=33 onset_rel_s=250.505 persistence_bins=31
values_compact=delta:14252781568,0,32002048,-3497984,1081344,1081344,-1949696,-1323008,-268288,-268288,-425984,-10522624,-282624,-282624,-647168,-671744,-315392,-315392,57880576,-954368,-4745216,-4745216,-1220608,-9576448,-608256,-608256,-1269760,0,-1187840,7122944,-4853760,-4853760,32325632,218750976,-9080832,-9080832,-442368,234180608,-260096,-260096,-8896512,-630784,-303104,-303104,-716800,-671744,-4714496,-4714496,-1110016,-1077248,-579584,-579584,-1212416,57483264,7843840,7843840,-9785344,-1830912,-7278592,-7278592,-2088960,0,7356416,-450560
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1
[M9] rank=9 service=ts-cancel-service metric=container.filesystem.available baseline=14288188074.666666 peak=14810349568.0 signed_z=26.602 onset_bin=33 onset_rel_s=250.505 persistence_bins=31
values_compact=delta:14252781568,0,32002048,-3497984,1081344,1081344,-1949696,-1323008,-268288,-268288,-425984,-10522624,-282624,-282624,-647168,-671744,-315392,-315392,57880576,-954368,-4745216,-4745216,-1220608,-9576448,-608256,-608256,-1269760,0,-1187840,7122944,-4853760,-4853760,32325632,218750976,-9080832,-9080832,-442368,234180608,-260096,-260096,-8896512,-630784,-303104,-303104,-716800,-671744,-4714496,-4714496,-1110016,-1077248,-579584,-579584,-1212416,57483264,7843840,7843840,-9785344,-1830912,-7278592,-7278592,-2088960,0,7356416,-450560
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1
[M10] rank=10 service=ts-delivery-service metric=container.filesystem.available baseline=14288188074.666666 peak=14810349568.0 signed_z=26.602 onset_bin=33 onset_rel_s=250.505 persistence_bins=31
values_compact=delta:14252781568,0,32002048,-3497984,1081344,1081344,-1949696,-1323008,-268288,-268288,-425984,-10522624,-282624,-282624,-647168,-671744,-315392,-315392,57880576,-954368,-4745216,-4745216,-1220608,-9576448,-608256,-608256,-1269760,0,-1187840,7122944,-4853760,-4853760,32325632,218750976,-9080832,-9080832,-442368,234180608,-260096,-260096,-8896512,-630784,-303104,-303104,-716800,-671744,-4714496,-4714496,-1110016,-1077248,-579584,-579584,-1212416,57483264,7843840,7843840,-9785344,-1830912,-7278592,-7278592,-2088960,0,7356416,-450560
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1
[M11] rank=11 service=ts-food-service metric=container.filesystem.available baseline=14288188074.666666 peak=14810349568.0 signed_z=26.602 onset_bin=33 onset_rel_s=250.505 persistence_bins=31
values_compact=delta:14252781568,0,32002048,-3497984,1081344,1081344,-1949696,-1323008,-268288,-268288,-425984,-10522624,-282624,-282624,-647168,-671744,-315392,-315392,57880576,-954368,-4745216,-4745216,-1220608,-9576448,-608256,-608256,-1269760,0,-1187840,7122944,-4853760,-4853760,32325632,218750976,-9080832,-9080832,-442368,234180608,-260096,-260096,-8896512,-630784,-303104,-303104,-716800,-671744,-4714496,-4714496,-1110016,-1077248,-579584,-579584,-1212416,57483264,7843840,7843840,-9785344,-1830912,-7278592,-7278592,-2088960,0,7356416,-450560
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1
[M12] rank=12 service=ts-gateway-service metric=container.filesystem.available baseline=14288188074.666666 peak=14810349568.0 signed_z=26.602 onset_bin=33 onset_rel_s=250.505 persistence_bins=31
values_compact=delta:14252781568,0,32002048,-3497984,1081344,1081344,-1949696,-1323008,-268288,-268288,-425984,-10522624,-282624,-282624,-647168,-671744,-315392,-315392,57880576,-954368,-4745216,-4745216,-1220608,-9576448,-608256,-608256,-1269760,0,-1187840,7122944,-4853760,-4853760,32325632,218750976,-9080832,-9080832,-442368,234180608,-260096,-260096,-8896512,-630784,-303104,-303104,-716800,-671744,-4714496,-4714496,-1110016,-1077248,-579584,-579584,-1212416,57483264,7843840,7843840,-9785344,-1830912,-7278592,-7278592,-2088960,0,7356416,-450560
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[315.16123390197754,475.4626522064209]

=== LOG SUMMARY ===
{"entries":[{"error_logs":1904,"error_pct":19.59,"service":"ts-seat-service","total_logs":9720},{"error_logs":261,"error_pct":19.49,"service":"ts-food-service","total_logs":1339},{"error_logs":96,"error_pct":25.0,"service":"ts-delivery-service","total_logs":384},{"error_logs":95,"error_pct":25.0,"service":"ts-notification-service","total_logs":380},{"error_logs":57,"error_pct":1.26,"service":"ts-ui-dashboard","total_logs":4516},{"error_logs":55,"error_pct":1.24,"service":"ts-travel-service","total_logs":4434},{"error_logs":18,"error_pct":2.27,"service":"ts-preserve-service","total_logs":792},{"error_logs":18,"error_pct":0.53,"service":"ts-order-service","total_logs":3366}],"mode":"errors","omitted_services":22,"service_count":30}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":-69.6,"error_pct":0.0,"p95_during_ms":8.303433800000002,"p95_pre_ms":27.298636599999966,"service":"ts-train-food-service","spans":1508},{"delta_pct":-55.1,"error_pct":0.0,"p95_during_ms":5.902941349999997,"p95_pre_ms":13.140294299999944,"service":"ts-order-other-service","spans":5640},{"delta_pct":-52.0,"error_pct":28.51,"p95_during_ms":29.408227299999982,"p95_pre_ms":61.26808634999999,"service":"ts-food-service","spans":1383},{"delta_pct":-47.9,"error_pct":0.0,"p95_during_ms":16.460297499999996,"p95_pre_ms":31.61237925,"service":"ts-consign-service","spans":579},{"delta_pct":-46.5,"error_pct":0.0,"p95_during_ms":5.510795549999999,"p95_pre_ms":10.297147800000003,"service":"ts-order-service","spans":8920},{"delta_pct":-45.9,"error_pct":0.0,"p95_during_ms":8.455336199999996,"p95_pre_ms":15.622362699999998,"service":"ts-contacts-service","spans":1700},{"delta_pct":-44.7,"error_pct":0.0,"p95_during_ms":6.051633749999998,"p95_pre_ms":10.938985899999997,"service":"ts-price-service","spans":2345},{"delta_pct":-43.5,"error_pct":0.0,"p95_during_ms":21.15146025,"p95_pre_ms":37.4312125,"service":"ts-seat-service","spans":7766}],"omitted_services":21,"service_count":29}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=35 omitted_edges=1
[{"evidence_source":"trace","onset_rel_s":34.8,"rank":1,"service":"ts-cancel-service","severity_z":7.707},{"evidence_source":"metric","onset_rel_s":280.2,"rank":2,"service":"ts-assurance-service","severity_z":26.602},{"evidence_source":"metric","onset_rel_s":280.2,"rank":3,"service":"ts-delivery-service","severity_z":26.602},{"evidence_source":"metric","onset_rel_s":280.2,"rank":4,"service":"ts-gateway-service","severity_z":26.602},{"evidence_source":"metric","onset_rel_s":280.2,"rank":5,"service":"ts-route-plan-service","severity_z":26.602},{"evidence_source":"metric","onset_rel_s":280.2,"rank":6,"service":"ts-station-food-service","severity_z":26.602},{"evidence_source":"metric","onset_rel_s":280.2,"rank":7,"service":"ts-ui-dashboard","severity_z":26.602},{"evidence_source":"metric","onset_rel_s":293.4,"rank":8,"service":"ts-config-service","severity_z":17.559},{"evidence_source":"trace","onset_rel_s":324.0,"rank":9,"service":"ts-price-service","severity_z":100.955},{"evidence_source":"metric","onset_rel_s":375.0,"rank":10,"service":"ts-verification-code-service","severity_z":21.072},{"evidence_source":"metric","onset_rel_s":410.4,"rank":11,"service":"loadgenerator","severity_z":156.432},{"evidence_source":"trace","onset_rel_s":443.4,"rank":12,"service":"ts-food-service","severity_z":19.428},{"evidence_source":"trace","onset_rel_s":453.6,"rank":13,"service":"ts-station-service","severity_z":54.834},{"evidence_source":"trace","onset_rel_s":473.4,"rank":14,"service":"ts-contacts-service","severity_z":21.597}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"ts-ui-dashboard","caller":"loadgenerator"},{"callee":"ts-station-food-service","caller":"ts-food-service"},{"callee":"ts-assurance-service","caller":"ts-ui-dashboard"},{"callee":"ts-cancel-service","caller":"ts-ui-dashboard"},{"callee":"ts-contacts-service","caller":"ts-ui-dashboard"},{"callee":"ts-food-service","caller":"ts-ui-dashboard"},{"callee":"ts-verification-code-service","caller":"ts-ui-dashboard"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

[excluded before optimizer]

# Causal SFT v2 base rollout — INC-E3CC86BC792F

## System

You are an expert Site Reliability Engineer performing Root Cause Analysis (RCA) for a microservice application deployed on a Kubernetes cluster. A fault has occurred in the system. Your task is to identify the root cause of the incident.

Root causes can occur at three levels:
- Pod level: a specific container replica (e.g., "cartservice-0")
- Service level: a microservice type (e.g., "paymentservice") — predict any pod of that service
- Node level: an infrastructure host (e.g., "node-6") — nodes appear as isolated entities with system metrics (CPU, memory, network, disk) but no application logs or traces

The system consists of multiple services communicating over HTTP/gRPC, running on shared infrastructure nodes. A fault in one component (pod, service, or node) can propagate to dependent components, causing them to appear degraded even though they are not the root cause.

Node-level faults (e.g., host memory exhaustion, CPU saturation, disk I/O) often manifest as correlated anomalies across multiple pods. If several unrelated pods show simultaneous degradation and a node shows critical system-level metrics, the node is likely the root cause.

Focus on distinguishing the ORIGIN of the fault from its SYMPTOMS in downstream or co-located components.

## User

[image: RQs/RQ0/results/causal_integration_sft_v1/data/cases/INC-E3CC86BC792F/dashboard.png]

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
opaque_id: INC-E3CC86BC792F
observation_window={"duration_rel_s":477.442,"source_metric_rows":950}
selection_summary={"candidate_count":104,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":916,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["loadgenerator","loadgenerator-77d5b896cb-wndqx","mysql","mysql-0","rabbitmq","rabbitmq-0","ts-admin-basic-info-service","ts-admin-basic-info-service-66cdcc94bc-lms89","ts-admin-order-service","ts-admin-order-service-5b6dc77d7d-6crkx","ts-admin-route-service","ts-admin-route-service-f9c84f85f-vlc2x","ts-admin-travel-service","ts-admin-travel-service-659b5c9df4-7t4gt","ts-admin-user-service","ts-admin-user-service-5bfc8844b9-wfcqs","ts-assurance-service","ts-assurance-service-75c854dc5c-xfcwv","ts-auth-service","ts-auth-service-69bdd5df8-zwdk7","ts-avatar-service","ts-avatar-service-845b64df6-tjhr9","ts-basic-service","ts-basic-service-7c6d59d5c4-mrvj9","ts-cancel-service","ts-cancel-service-7ffd988fdb-d9692","ts-config-service","ts-config-service-55cffbf48b-dx8rc","ts-consign-price-service","ts-consign-price-service-654cb4fc65-x9cmn","ts-consign-service","ts-consign-service-9954fddf-l6cms","ts-contacts-service","ts-contacts-service-6d745b6c8f-4zqsc","ts-delivery-service","ts-delivery-service-694895c6cb-dzn5m","ts-execute-service","ts-execute-service-8457c56cb7-899gb","ts-food-delivery-service","ts-food-delivery-service-96d856899-87j6b","ts-food-service","ts-food-service-64d454885b-6sxqg","ts-gateway-service","ts-gateway-service-7f988fb8c4-gm4ll","ts-inside-payment-service","ts-inside-payment-service-5ccb8ccb87-mn9wh","ts-news-service","ts-news-service-6d6c6d7855-hkr55","ts-notification-service","ts-notification-service-58f6c468d7-vq7d9","ts-order-other-service","ts-order-other-service-5d6878687f-drl2s","ts-order-service","ts-order-service-6794d6f564-btq98","ts-payment-service","ts-payment-service-58854d694-fffmt","ts-preserve-other-service","ts-preserve-other-service-64fd9c88cf-xdzbk","ts-preserve-service","ts-preserve-service-696df489d4-k46sp","ts-price-service","ts-price-service-67c895b45-g6qsm","ts-rebook-service","ts-rebook-service-7c7644bbdd-5vs6q","ts-route-plan-service","ts-route-plan-service-556cddc5c9-c74nj","ts-route-service","ts-route-service-cfc6dbcf7-lxx9v","ts-seat-service","ts-seat-service-6c78b7d797-rlnjn","ts-security-service","ts-security-service-55f5b777bb-tm5rw","ts-station-food-service","ts-station-food-service-746f6779d7-kfmsh","ts-station-service","ts-station-service-65986cc944-8z28q","ts-ticket-office-service","ts-ticket-office-service-d7c58b8c7-kzvvr","ts-train-food-service","ts-train-food-service-d5485c677-gh7dw","ts-train-service","ts-train-service-9b56d75b6-dnktt","ts-travel-plan-service","ts-travel-plan-service-7875c49896-qn8gz","ts-travel-service","ts-travel-service-c7b5c6d9b-n28x9","ts-travel2-service","ts-travel2-service-7ff5bbbf54-w2tpn","ts-ui-dashboard","ts-ui-dashboard-57867cb85c-dqfbs","ts-user-service","ts-user-service-54dd6b48c-q5g67","ts-verification-code-service","ts-verification-code-service-85785c4f79-5nz8l","ts-voucher-service","ts-voucher-service-689c4fc885-9t2lw","ts-wait-order-service","ts-wait-order-service-7cf6bc9468-x7vnm","worker1","worker2","worker3","worker4","worker5","worker6"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[3.73,11.19,18.65,26.11,33.57,41.03,48.49,55.95,63.41,70.87,78.33,85.79,93.25,100.71,108.17,115.631,123.091,130.551,138.011,145.471,152.931,160.391,167.851,175.311,182.771,190.231,197.691,205.151,212.611,220.071,227.531,234.991,242.451,249.911,257.371,264.831,272.291,279.751,287.211,294.671,302.131,309.591,317.051,324.511,331.971,339.431,346.892,354.352,361.812,369.272,376.732,384.192,391.652,399.112,406.572,414.032,421.492,428.952,436.412,443.872,451.332,458.792,466.252,473.712]
[M1] rank=1 service=ts-config-service-55cffbf48b-dx8rc metric=k8s.container.ready baseline=1.0 peak=0.0 signed_z=-999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,-1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0001000100010001000100010001000100010001000100010001000100010010
observed_counts_compact=csv:1,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,0,1
[M2] rank=2 service=ts-config-service-55cffbf48b-dx8rc metric=k8s.container.restarts baseline=0.0 peak=1.0 signed_z=999.0 onset_bin=36 onset_rel_s=272.291 persistence_bins=21
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0001000100010001000100010001000100010001000100010001000100010010
observed_counts_compact=csv:1,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,0,1
[M3] rank=3 service=ts-config-service metric=k8s.deployment.available baseline=1.0 peak=0.0 signed_z=-999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,-1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0001000100010001000100010001000100010001000100010001000100010010
observed_counts_compact=csv:1,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,0,1
[M4] rank=4 service=ts-voucher-service metric=k8s.pod.memory.node.utilization baseline=0.000293 peak=0.000293 signed_z=999.0 onset_bin=0 onset_rel_s=3.73 persistence_bins=64
values_compact=rle:0.000293*64
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,1,2,1,2,1,2,1,2,1,2,1
[M5] rank=5 service=ts-voucher-service metric=k8s.pod.memory_limit_utilization baseline=0.012263 peak=0.012264 signed_z=999.0 onset_bin=0 onset_rel_s=3.73 persistence_bins=64
values_compact=rle:0.012263*60,0.012264*4
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,1,2,1,2,1,2,1,2,1,2,1
[M6] rank=6 service=ts-config-service metric=container.filesystem.usage baseline=466944.0 peak=3080192.0 signed_z=848.404 onset_bin=33 onset_rel_s=249.911 persistence_bins=11
values_compact=rle:466944*33,1773568*1,3080192*1,0*1,69632*1,256000*1,442368*6,466944*20
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M7] rank=7 service=ts-config-service metric=k8s.pod.memory.rss baseline=770415189.333333 peak=119693312.0 signed_z=-241.363 onset_bin=33 onset_rel_s=249.911 persistence_bins=16
values_compact=delta:767950848,585728,0,1454080,0,-77824,0,98304,0,-2224128,12288,12288,0,0,0,53248,0,0,0,1323008,0,671744,0,4521984,0,4096,0,0,0,102400,0,0,0,270372864,0,-925167616,153686016,0,0,199831552,0,55271424,55271424,43188224,43188224,0,80822272,0,9154560,5447680,5447680,0,3608576,0,0,712704,352256,0,0,897024,0,249856,0,978944
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M8] rank=8 service=ts-config-service metric=k8s.pod.memory.available baseline=2439327658.666667 peak=3092414464.0 signed_z=234.862 onset_bin=33 onset_rel_s=249.911 persistence_bins=17
values_compact=delta:2441758720,-452608,0,-1671168,0,331776,0,-102400,0,2199552,-8192,-8192,0,0,0,-585728,532480,0,0,-1323008,0,-671744,0,-4542464,0,-270336,-16384,0,0,-356352,0,536576,0,-523661312,0,1180725248,-153624576,0,0,-204042240,0,-54059008,-54059008,-50079744,-50079744,0,-74604544,0,-3727360,-5840896,-5840896,0,-4284416,0,0,1748992,-1560576,0,0,-421888,0,-512000,0,-1245184
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M9] rank=9 service=ts-config-service metric=k8s.pod.memory.working_set baseline=781897813.333333 peak=128811008.0 signed_z=-234.862 onset_bin=33 onset_rel_s=249.911 persistence_bins=17
values_compact=delta:779466752,452608,0,1671168,0,-331776,0,102400,0,-2199552,8192,8192,0,0,0,585728,-532480,0,0,1323008,0,671744,0,4542464,0,270336,16384,0,0,356352,0,-536576,0,523661312,0,-1180725248,153624576,0,0,204042240,0,54059008,54059008,50079744,50079744,0,74604544,0,3727360,5840896,5840896,0,4284416,0,0,-1748992,1560576,0,0,421888,0,512000,0,1245184
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M10] rank=10 service=ts-config-service metric=k8s.pod.memory.node.utilization baseline=0.005793 peak=0.001013 signed_z=-232.109 onset_bin=33 onset_rel_s=249.911 persistence_bins=27
values_compact=rle:0.005775*1,0.005779*2,0.005791*2,0.005789*4,0.005773*6,0.005778*1,0.005774*3,0.005783*2,0.005788*2,0.005822*2,0.005824*4,0.005827*2,0.005823*2,0.009701*2,0.001013*1,0.002151*3,0.003665*2,0.004065*1,0.004466*1,0.004836*1,0.005207*2,0.00576*2,0.005787*1,0.005831*1,0.005874*2,0.005906*3,0.005893*1,0.005904*3,0.005907*2,0.005911*2,0.00592*1
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M11] rank=11 service=ts-config-service metric=k8s.pod.memory_limit_utilization baseline=0.242853 peak=0.042484 signed_z=-232.109 onset_bin=33 onset_rel_s=249.911 persistence_bins=27
values_compact=delta:0.242098,0.00014,0,0.000519,0,-0.000103,0,0.000032,0,-0.000683,0.000003,0.000002,0,0,0,0.000182,-0.000165,0,0,0.00041,0,0.000209,0,0.00141,0,0.000084,0.000005,0,0,0.000111,0,-0.000167,0,0.162556,0,-0.364159,0.047692,0,0,0.063452,0,0.016782,0.016782,0.015547,0.015547,0,0.02316,0,0.001157,0.001814,0.001813,0,0.00133,0,0,-0.000543,0.000484,0,0,0.000131,0,0.000159,0,0.000387
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2
[M12] rank=12 service=ts-config-service metric=k8s.pod.memory.usage baseline=782282837.333333 peak=136851456.0 signed_z=-232.109 onset_bin=33 onset_rel_s=249.911 persistence_bins=27
values_compact=delta:779851776,452608,0,1671168,0,-331776,0,102400,0,-2199552,8192,8192,0,0,0,585728,-532480,0,0,1323008,0,671744,0,4542464,0,270336,16384,0,0,356352,0,-536576,0,523628544,0,-1173037056,153624576,0,0,204394496,0,54059008,54059008,50079744,50079744,0,74604544,0,3727360,5840896,5840896,0,4284416,0,0,-1748992,1560576,0,0,421888,0,512000,0,1245184
missing_mask_bits=0000000000000000000000000000000000000000000000000000000000000000
observed_counts_compact=csv:2,1,2,1,2,1,2,1,2,1,2,1,2,1,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[259.9994366168976,469.999826669693]

=== LOG SUMMARY ===
{"entries":[{"error_logs":4595,"error_pct":19.8,"service":"ts-seat-service","total_logs":23202},{"error_logs":445,"error_pct":16.44,"service":"ts-food-service","total_logs":2707},{"error_logs":158,"error_pct":5.59,"service":"ts-preserve-service","total_logs":2829},{"error_logs":158,"error_pct":1.84,"service":"ts-order-service","total_logs":8564},{"error_logs":96,"error_pct":25.0,"service":"ts-notification-service","total_logs":384},{"error_logs":96,"error_pct":25.0,"service":"ts-delivery-service","total_logs":384},{"error_logs":73,"error_pct":1.4,"service":"ts-travel2-service","total_logs":5232},{"error_logs":57,"error_pct":3.2,"service":"ts-route-plan-service","total_logs":1783}],"mode":"errors","omitted_services":23,"service_count":31}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":-38.4,"error_pct":0.0,"p95_during_ms":14.812379299999998,"p95_pre_ms":24.040092049999966,"service":"ts-payment-service","spans":390},{"delta_pct":-37.7,"error_pct":2.43,"p95_during_ms":88.34440824999986,"p95_pre_ms":141.87491859999994,"service":"ts-travel-service","spans":12931},{"delta_pct":-37.0,"error_pct":0.0,"p95_during_ms":35.8584334,"p95_pre_ms":56.946288149999965,"service":"ts-basic-service","spans":10471},{"delta_pct":-35.4,"error_pct":0.0,"p95_during_ms":8.413709499999998,"p95_pre_ms":13.02373639999999,"service":"ts-station-food-service","spans":2265},{"delta_pct":-35.2,"error_pct":0.0,"p95_during_ms":4.643592249999999,"p95_pre_ms":7.165894649999998,"service":"ts-price-service","spans":6700},{"delta_pct":-34.1,"error_pct":0.0,"p95_during_ms":4.872719200000001,"p95_pre_ms":7.392369,"service":"ts-train-food-service","spans":3258},{"delta_pct":-33.9,"error_pct":0.0,"p95_during_ms":8.607392949999992,"p95_pre_ms":13.01724975,"service":"ts-assurance-service","spans":938},{"delta_pct":-33.4,"error_pct":0.0,"p95_during_ms":356.85565529999997,"p95_pre_ms":535.6157875999999,"service":"ts-preserve-service","spans":1832}],"omitted_services":22,"service_count":30}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=35 omitted_edges=0
[{"evidence_source":"metric","onset_rel_s":242.4,"rank":1,"service":"ts-train-food-service","severity_z":13.7},{"evidence_source":"trace","onset_rel_s":293.4,"rank":2,"service":"ts-order-service","severity_z":146.004},{"evidence_source":"metric","onset_rel_s":298.2,"rank":3,"service":"ts-route-plan-service","severity_z":36.598},{"evidence_source":"metric","onset_rel_s":301.2,"rank":4,"service":"ts-travel-plan-service","severity_z":21.029},{"evidence_source":"trace","onset_rel_s":333.0,"rank":5,"service":"ts-config-service","severity_z":31.924},{"evidence_source":"metric","onset_rel_s":345.6,"rank":6,"service":"mysql","severity_z":33.78},{"evidence_source":"metric","onset_rel_s":351.0,"rank":7,"service":"ts-seat-service","severity_z":17.304},{"evidence_source":"metric","onset_rel_s":352.8,"rank":8,"service":"ts-route-service","severity_z":16.95},{"evidence_source":"metric","onset_rel_s":426.0,"rank":9,"service":"ts-station-food-service","severity_z":13.553},{"evidence_source":"metric","onset_rel_s":426.6,"rank":10,"service":"loadgenerator","severity_z":22.224},{"evidence_source":"metric","onset_rel_s":445.8,"rank":11,"service":"rabbitmq","severity_z":62.398},{"evidence_source":"metric","onset_rel_s":448.2,"rank":12,"service":"ts-voucher-service","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":448.2,"rank":13,"service":"ts-preserve-service","severity_z":36.146},{"evidence_source":"metric","onset_rel_s":466.8,"rank":14,"service":"ts-security-service","severity_z":20.603}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"ts-order-service","caller":"ts-preserve-service"},{"callee":"ts-seat-service","caller":"ts-preserve-service"},{"callee":"ts-security-service","caller":"ts-preserve-service"},{"callee":"ts-route-service","caller":"ts-route-plan-service"},{"callee":"ts-config-service","caller":"ts-seat-service"},{"callee":"ts-order-service","caller":"ts-seat-service"},{"callee":"ts-order-service","caller":"ts-security-service"},{"callee":"ts-route-plan-service","caller":"ts-travel-plan-service"},{"callee":"ts-seat-service","caller":"ts-travel-plan-service"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

## Assistant

{
"services": [
"ts-config-service-55cffbf48b-dx8rc",
"ts-config-service",
"ts-seat-service",
"ts-order-service",
"ts-train-food-service"
],
"reason": "The root cause is the crash of the ts-config-service pod (ts-config-service-55cffbf48b-dx8rc), evidenced by the container becoming not ready and restarting at t=272s, which caused a sharp drop in memory usage and propagated failures to dependent services like ts-seat-service and ts-order-service.",
"confidence": "high"
}
